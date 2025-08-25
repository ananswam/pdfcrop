#!/usr/bin/env python3
"""
PDF Auto-Cropper for E-ink Devices
Automatically crops PDF pages to remove margins and creates uniform-sized pages.
"""

import argparse
import sys
from pathlib import Path
import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QFileDialog, QMessageBox,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QGraphicsRectItem, QSpinBox)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPen, QBrush


def get_content_bbox(page, threshold=0.95, footer_height_ratio=0.1):
    """
    Analyze a PDF page to find the bounding box of actual content.
    Returns the bounding box as (x0, y0, x1, y1) in PDF coordinates.
    Uses special logic to ignore footer content like page numbers.
    """
    # Convert page to image for analysis
    mat = fitz.Matrix(2, 2)  # 2x zoom for better detection
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Convert to grayscale and then to numpy array
    gray = img.convert('L')
    img_array = np.array(gray)
    
    # Find non-white pixels (content)
    # Using threshold to account for slight color variations
    content_mask = img_array < (255 * threshold)
    
    # Find the bounding box of content
    rows = np.any(content_mask, axis=1)
    cols = np.any(content_mask, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        # If no content found, return full page
        return page.rect
    
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    
    # Special handling for bottom footer content
    # Check if there's isolated content in the bottom portion that might be footer
    page_height = img_array.shape[0]
    footer_start = int(page_height * (1 - footer_height_ratio))
    
    # Look for content in the footer area
    footer_rows = rows[footer_start:]
    if np.any(footer_rows):
        # Find gaps in content - if there's a significant gap before footer content,
        # treat the footer as separate from main content
        main_content_end = y_max
        
        # Look for the last significant content before potential footer
        # Check for gaps larger than 2% of page height
        gap_threshold = int(page_height * 0.02)
        
        # Scan backwards from y_max to find large gaps
        content_rows = np.where(rows)[0]
        for i in range(len(content_rows) - 1, 0, -1):
            gap_size = content_rows[i] - content_rows[i-1]
            if gap_size > gap_threshold and content_rows[i] > footer_start:
                # Found a significant gap and we're in footer territory
                main_content_end = content_rows[i-1]
                break
        
        # Use the adjusted end point if we found a reasonable break
        if main_content_end < y_max and main_content_end > y_min:
            y_max = main_content_end
    
    # Convert back to PDF coordinates (accounting for 2x zoom)
    page_rect = page.rect
    x0 = page_rect.x0 + (x_min / 2)
    y0 = page_rect.y0 + (y_min / 2)
    x1 = page_rect.x0 + (x_max / 2)
    y1 = page_rect.y0 + (y_max / 2)
    
    return fitz.Rect(x0, y0, x1, y1)


def analyze_pdf_margins(pdf_path, sample_pages=99999999, buffer=0.01, footer_height_ratio=0.1):
    """
    Analyze a PDF to determine optimal crop margins.
    Returns suggested crop values as (left, top, right, bottom) percentages.
    """
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    
    # Sample pages evenly distributed throughout the document
    if page_count <= sample_pages:
        sample_indices = range(page_count)
    else:
        step = page_count // sample_pages
        sample_indices = range(0, page_count, step)[:sample_pages]
    
    content_boxes = []
    page_sizes = []
    
    print(f"Analyzing {len(sample_indices)} pages to determine optimal crop...")
    
    for i in sample_indices:
        page = doc[i]
        page_rect = page.rect
        content_bbox = get_content_bbox(page, footer_height_ratio=footer_height_ratio)
        
        content_boxes.append(content_bbox)
        page_sizes.append(page_rect)
    
    doc.close()
    
    # Calculate margin percentages for each page
    left_margins = []
    top_margins = []
    right_margins = []
    bottom_margins = []
    
    for content_box, page_rect in zip(content_boxes, page_sizes):
        left_margin = (content_box.x0 - page_rect.x0) / page_rect.width
        top_margin = (content_box.y0 - page_rect.y0) / page_rect.height
        right_margin = (page_rect.x1 - content_box.x1) / page_rect.width
        bottom_margin = (page_rect.y1 - content_box.y1) / page_rect.height
        
        left_margins.append(max(0, left_margin))
        top_margins.append(max(0, top_margin))
        right_margins.append(max(0, right_margin))
        bottom_margins.append(max(0, bottom_margin))
    
    # Use conservative estimates (smaller margins to avoid cutting content)
    # Add a small buffer to prevent content from being too close to edges
    suggested_left = max(0, np.percentile(left_margins, 25) - buffer)
    suggested_top = max(0, np.percentile(top_margins, 25) - buffer)
    suggested_right = max(0, np.percentile(right_margins, 25) - buffer)
    suggested_bottom = max(0, np.percentile(bottom_margins, 25) - buffer)
    
    return suggested_left, suggested_top, suggested_right, suggested_bottom


def crop_pdf(input_path, output_path, left=None, top=None, right=None, bottom=None, buffer=0.01,
             footer_height_ratio=0.1, optimize=True):
    """
    Crop a PDF with specified margins (as percentages) and create uniform pages.
    """
    doc = fitz.open(input_path)
    
    # If no crop values provided, analyze the PDF to determine them
    if None in [left, top, right, bottom]:
        print("No crop values provided. Analyzing PDF for optimal cropping...")
        auto_left, auto_top, auto_right, auto_bottom = analyze_pdf_margins(input_path, buffer=buffer, footer_height_ratio=footer_height_ratio)
        
        left = left if left is not None else auto_left
        top = top if top is not None else auto_top
        right = right if right is not None else auto_right
        bottom = bottom if bottom is not None else auto_bottom
        
        print(f"Suggested crop margins: L={left:.3f}, T={top:.3f}, R={right:.3f}, B={bottom:.3f}")
    
    # First pass: determine the maximum content dimensions after cropping
    max_width = 0
    max_height = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_rect = page.rect
        
        # Calculate crop rectangle
        crop_left = page_rect.x0 + (page_rect.width * left)
        crop_top = page_rect.y0 + (page_rect.height * top)
        crop_right = page_rect.x1 - (page_rect.width * right)
        crop_bottom = page_rect.y1 - (page_rect.height * bottom)
        
        cropped_width = crop_right - crop_left
        cropped_height = crop_bottom - crop_top
        
        max_width = max(max_width, cropped_width)
        max_height = max(max_height, cropped_height)
    
    print(f"Uniform page size will be: {max_width:.1f} x {max_height:.1f} points")
    
    # Second pass: crop and resize pages to uniform size
    output_doc = fitz.open()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_rect = page.rect
        
        # Calculate crop rectangle
        crop_left = page_rect.x0 + (page_rect.width * left)
        crop_top = page_rect.y0 + (page_rect.height * top)
        crop_right = page_rect.x1 - (page_rect.width * right)
        crop_bottom = page_rect.y1 - (page_rect.height * bottom)
        
        crop_rect = fitz.Rect(crop_left, crop_top, crop_right, crop_bottom)
        
        # Create new page with uniform size
        new_page = output_doc.new_page(width=max_width, height=max_height)
        
        # Calculate scaling and positioning to fit cropped content
        cropped_width = crop_rect.width
        cropped_height = crop_rect.height
        
        scale_x = max_width / cropped_width if cropped_width > 0 else 1
        scale_y = max_height / cropped_height if cropped_height > 0 else 1
        scale = min(scale_x, scale_y)  # Use smaller scale to fit entirely
        
        # Center the content
        scaled_width = cropped_width * scale
        scaled_height = cropped_height * scale
        offset_x = (max_width - scaled_width) / 2
        offset_y = (max_height - scaled_height) / 2
        
        # Create transformation matrix
        mat = fitz.Matrix(scale, scale).pretranslate(offset_x - crop_left * scale, 
                                                   offset_y - crop_top * scale)
        
        # Calculate target rectangle for the content
        target_rect = fitz.Rect(offset_x, offset_y, offset_x + scaled_width, offset_y + scaled_height)
        
        # Insert the cropped page content into the target rectangle
        new_page.show_pdf_page(target_rect, doc, page_num, clip=crop_rect)

        # add log line every 20 pages
        if page_num % 20 == 0:
            print(f"Processed page {page_num} of {len(doc)}")
    
    # Store page counts before closing documents
    original_page_count = len(doc)
    output_page_count = len(output_doc)
    
    # Save the output
    print(f"Saving cropped PDF to {output_path}...")
    garbage, deflate = (4, True) if optimize else (0, False)
    output_doc.save(output_path, garbage=garbage, deflate=deflate)
    output_doc.close()
    doc.close()
    
    print(f"Successfully created cropped PDF: {output_path}")
    print(f"Original pages: {original_page_count}, Output pages: {output_page_count}")


class PDFCropView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.crop_rect = None
        self.selection_rect = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.start_pos = scene_pos
            if self.selection_rect:
                self.scene.removeItem(self.selection_rect)
                self.selection_rect = None
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if hasattr(self, 'start_pos') and event.buttons() & Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, scene_pos).normalized()
            
            if self.selection_rect:
                self.scene.removeItem(self.selection_rect)
                
            pen = QPen(Qt.GlobalColor.red, 2)
            brush = QBrush(Qt.GlobalColor.transparent)
            self.selection_rect = self.scene.addRect(rect, pen, brush)
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'start_pos') and self.selection_rect:
            self.crop_rect = self.selection_rect.rect()
        super().mouseReleaseEvent(event)


class PDFCropGUI(QMainWindow):
    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.current_page = 0
        self.scale_factor = 1.0
        self.persistent_crop_rect = None  # Store crop selection across pages
        self.min_page = 1  # 1-based page numbers for display
        self.max_page = len(self.doc)
        self.preview_crop_range_only = False  # Preview mode flag
        
        self.setWindowTitle(f"PDF Cropper - {Path(pdf_path).name}")
        self.setGeometry(100, 100, 1000, 800)
        
        self.setup_ui()
        self.load_page()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        nav_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel()
        nav_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        nav_layout.addWidget(self.next_btn)
        
        nav_layout.addStretch()
        
        # Preview mode toggle
        self.preview_mode_btn = QPushButton("Preview Mode: All Pages")
        self.preview_mode_btn.clicked.connect(self.toggle_preview_mode)
        nav_layout.addWidget(self.preview_mode_btn)
        
        self.crop_btn = QPushButton("Crop PDF")
        self.crop_btn.clicked.connect(self.crop_pdf)
        nav_layout.addWidget(self.crop_btn)
        
        layout.addLayout(nav_layout)
        
        # Page range controls
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Crop pages from:"))
        
        self.min_page_spinbox = QSpinBox()
        self.min_page_spinbox.setMinimum(1)
        self.min_page_spinbox.setMaximum(len(self.doc))
        self.min_page_spinbox.setValue(1)
        self.min_page_spinbox.valueChanged.connect(self.update_page_range)
        range_layout.addWidget(self.min_page_spinbox)
        
        range_layout.addWidget(QLabel("to:"))
        
        self.max_page_spinbox = QSpinBox()
        self.max_page_spinbox.setMinimum(1)
        self.max_page_spinbox.setMaximum(len(self.doc))
        self.max_page_spinbox.setValue(len(self.doc))
        self.max_page_spinbox.valueChanged.connect(self.update_page_range)
        range_layout.addWidget(self.max_page_spinbox)
        
        self.range_info_label = QLabel(f"(Only pages {self.min_page}-{self.max_page} will be cropped and shown in preview)")
        range_layout.addWidget(self.range_info_label)
        range_layout.addStretch()
        
        layout.addLayout(range_layout)
        
        # PDF view
        self.pdf_view = PDFCropView()
        layout.addWidget(self.pdf_view)
        
        # Instructions
        instructions = QLabel("Click and drag to select crop area")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
    def load_page(self):
        page = self.doc[self.current_page]
        
        # Get the page's media box to ensure proper boundaries
        page_rect = page.rect
        
        # Use identity matrix first, then scale
        mat = fitz.Matrix(1, 1)  # Start with identity
        mat = mat.prescale(2, 2)  # Then scale by 2
        
        # Render with explicit clip to page boundaries
        pix = page.get_pixmap(matrix=mat, clip=page_rect, alpha=False)
        
        # Direct conversion to QImage
        img_format = QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        
        # Create a copy to avoid memory issues
        qimg = qimg.copy()
        pixmap = QPixmap.fromImage(qimg)
        
        # Clear scene and add pixmap
        self.pdf_view.scene.clear()
        pixmap_item = self.pdf_view.scene.addPixmap(pixmap)
        
        # Add black border around the page
        border_pen = QPen(Qt.GlobalColor.black, 2)
        pixmap_rect = pixmap_item.boundingRect()
        self.pdf_view.scene.addRect(pixmap_rect, border_pen)
        
        self.pdf_view.fitInView(self.pdf_view.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Store info needed for coordinate conversion
        self.render_scale_factor = 2.0  # The zoom factor used in PDF rendering
        self.page_rect = page.rect
        self.pixmap_item = pixmap_item
        
        # Update page label and navigation buttons
        current_page_num = self.current_page + 1
        in_crop_range = self.min_page <= current_page_num <= self.max_page
        
        if in_crop_range:
            self.page_label.setText(f"Page {current_page_num} of {len(self.doc)} (WILL BE CROPPED)")
        else:
            self.page_label.setText(f"Page {current_page_num} of {len(self.doc)} (will keep original size)")
            
        # Update navigation button states based on preview mode
        if self.preview_crop_range_only:
            # In crop range preview mode
            prev_enabled = False
            next_enabled = False
            
            # Check if there are previous pages in crop range
            for p in range(self.current_page - 1, -1, -1):
                if self.min_page <= (p + 1) <= self.max_page:
                    prev_enabled = True
                    break
                    
            # Check if there are next pages in crop range
            for p in range(self.current_page + 1, len(self.doc)):
                if self.min_page <= (p + 1) <= self.max_page:
                    next_enabled = True
                    break
                    
            self.prev_btn.setEnabled(prev_enabled)
            self.next_btn.setEnabled(next_enabled)
        else:
            # In all pages mode
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page < len(self.doc) - 1)
        
        # Restore persistent selection if it exists
        if self.persistent_crop_rect:
            self.pdf_view.crop_rect = self.persistent_crop_rect
            # Redraw the selection rectangle
            pen = QPen(Qt.GlobalColor.red, 2)
            brush = QBrush(Qt.GlobalColor.transparent)
            self.pdf_view.selection_rect = self.pdf_view.scene.addRect(self.persistent_crop_rect, pen, brush)
        
    def prev_page(self):
        self.update_persistent_crop()
        if self.preview_crop_range_only:
            # Navigate within crop range only
            if self.current_page > 0:
                new_page = self.current_page - 1
                # Find previous page in crop range
                while new_page >= 0:
                    if self.min_page <= (new_page + 1) <= self.max_page:
                        self.current_page = new_page
                        break
                    new_page -= 1
        else:
            # Navigate all pages
            if self.current_page > 0:
                self.current_page -= 1
        self.load_page()
            
    def next_page(self):
        self.update_persistent_crop()
        if self.preview_crop_range_only:
            # Navigate within crop range only
            if self.current_page < len(self.doc) - 1:
                new_page = self.current_page + 1
                # Find next page in crop range
                while new_page < len(self.doc):
                    if self.min_page <= (new_page + 1) <= self.max_page:
                        self.current_page = new_page
                        break
                    new_page += 1
        else:
            # Navigate all pages
            if self.current_page < len(self.doc) - 1:
                self.current_page += 1
        self.load_page()
            
    def store_persistent_crop(self, crop_rect):
        """Store crop selection for persistence across page changes"""
        self.persistent_crop_rect = crop_rect
        
    def update_persistent_crop(self):
        """Update persistent crop from current selection"""
        if self.pdf_view.crop_rect:
            self.persistent_crop_rect = self.pdf_view.crop_rect
            
    def update_page_range(self):
        """Update the page range for cropping"""
        self.min_page = self.min_page_spinbox.value()
        self.max_page = self.max_page_spinbox.value()
        
        # Ensure min <= max
        if self.min_page > self.max_page:
            if self.sender() == self.min_page_spinbox:
                self.max_page_spinbox.setValue(self.min_page)
                self.max_page = self.min_page
            else:
                self.min_page_spinbox.setValue(self.max_page)
                self.min_page = self.max_page
        
        # Update the info label
        self.range_info_label.setText(f"(Only pages {self.min_page}-{self.max_page} will be cropped and shown in preview)")
        
        # Update the current page display
        self.load_page()
        
    def toggle_preview_mode(self):
        """Toggle between showing all pages and crop range only"""
        self.preview_crop_range_only = not self.preview_crop_range_only
        
        if self.preview_crop_range_only:
            self.preview_mode_btn.setText("Preview Mode: Crop Range Only")
            # Jump to first page in crop range if current page is outside range
            current_page_num = self.current_page + 1
            if not (self.min_page <= current_page_num <= self.max_page):
                self.current_page = self.min_page - 1  # Convert back to 0-based
        else:
            self.preview_mode_btn.setText("Preview Mode: All Pages")
            
        self.load_page()
            
    def crop_pdf(self):
        if not self.pdf_view.crop_rect:
            QMessageBox.warning(self, "No Selection", "Please select a crop area first.")
            return
            
        # Get output filename (default to Downloads directory)
        import os
        downloads_dir = os.path.expanduser("~/Downloads")
        default_filename = os.path.join(downloads_dir, f"{Path(self.pdf_path).stem}-cropped.pdf")
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Cropped PDF", 
            default_filename,
            "PDF files (*.pdf)"
        )
        
        if not output_path:
            return
            
        try:
            # Convert selection coordinates to PDF coordinates
            view_rect = self.pdf_view.crop_rect
            
            # The selection is in scene coordinates, which directly correspond to
            # the rendered pixmap coordinates. We need to convert back to PDF coordinates.
            pdf_x1 = view_rect.x() / self.render_scale_factor
            pdf_y1 = view_rect.y() / self.render_scale_factor
            pdf_x2 = (view_rect.x() + view_rect.width()) / self.render_scale_factor
            pdf_y2 = (view_rect.y() + view_rect.height()) / self.render_scale_factor
            
            # Clamp to page bounds
            pdf_x1 = max(0, min(pdf_x1, self.page_rect.width))
            pdf_y1 = max(0, min(pdf_y1, self.page_rect.height))
            pdf_x2 = max(0, min(pdf_x2, self.page_rect.width))
            pdf_y2 = max(0, min(pdf_y2, self.page_rect.height))
            
            crop_rect = fitz.Rect(pdf_x1, pdf_y1, pdf_x2, pdf_y2)
            
            # Analyze page sizes to find most common size
            from collections import Counter
            page_sizes = []
            for i in range(len(self.doc)):
                page = self.doc[i]
                # Round to nearest point to handle minor variations
                width = round(page.rect.width)
                height = round(page.rect.height)
                page_sizes.append((width, height))
            
            size_counts = Counter(page_sizes)
            most_common_size, most_common_count = size_counts.most_common(1)[0]
            total_pages = len(self.doc)
            most_common_fraction = most_common_count / total_pages
            
            # Log crop information
            original_width = self.page_rect.width
            original_height = self.page_rect.height
            cropped_width = crop_rect.width
            cropped_height = crop_rect.height
            
            left_cropped = pdf_x1
            top_cropped = pdf_y1
            right_cropped = original_width - pdf_x2
            bottom_cropped = original_height - pdf_y2
            
            print(f"\nPage Size Analysis:")
            print(f"Most common page size: {most_common_size[0]} x {most_common_size[1]} points")
            print(f"Pages with this size: {most_common_count}/{total_pages} ({most_common_fraction*100:.1f}%)")
            
            print(f"\nCrop Information (for pages matching most common size):")
            print(f"Original page size: {original_width:.1f} x {original_height:.1f} points")
            print(f"New page size: {cropped_width:.1f} x {cropped_height:.1f} points")
            print(f"Cropped from edges - Left: {left_cropped:.1f}, Top: {top_cropped:.1f}, Right: {right_cropped:.1f}, Bottom: {bottom_cropped:.1f} points")
            print(f"Crop percentages - Left: {left_cropped/original_width*100:.1f}%, Top: {top_cropped/original_height*100:.1f}%, Right: {right_cropped/original_width*100:.1f}%, Bottom: {bottom_cropped/original_height*100:.1f}%")
            
            # Apply crop only to pages in the specified range AND matching the most common size
            output_doc = fitz.open()
            cropped_pages = 0
            unchanged_pages = 0
            
            for page_num in range(len(self.doc)):
                page = self.doc[page_num]
                page_width = round(page.rect.width)
                page_height = round(page.rect.height)
                current_page_num = page_num + 1  # Convert to 1-based
                
                # Check if page is in crop range AND matches most common size
                if (self.min_page <= current_page_num <= self.max_page and 
                    (page_width, page_height) == most_common_size):
                    # Crop this page
                    cropped_width = crop_rect.width
                    cropped_height = crop_rect.height
                    new_page = output_doc.new_page(width=cropped_width, height=cropped_height)
                    
                    # Insert cropped content
                    target_rect = fitz.Rect(0, 0, cropped_width, cropped_height)
                    new_page.show_pdf_page(target_rect, self.doc, page_num, clip=crop_rect)
                    cropped_pages += 1
                else:
                    # Keep original page completely unchanged by inserting it directly
                    output_doc.insert_pdf(self.doc, from_page=page_num, to_page=page_num)
                    unchanged_pages += 1
                
            output_doc.save(output_path)
            output_doc.close()
            
            print(f"\nProcessing Summary:")
            print(f"Page range selected for cropping: {self.min_page}-{self.max_page}")
            print(f"Pages cropped: {cropped_pages}")
            print(f"Pages left unchanged: {unchanged_pages}")
            
            QMessageBox.information(self, "Success", f"Cropped PDF saved to {output_path}\nPage range {self.min_page}-{self.max_page}: Cropped {cropped_pages} pages, Unchanged {unchanged_pages} pages")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to crop PDF: {str(e)}")


def run_gui(pdf_path):
    app = QApplication(sys.argv)
    gui = PDFCropGUI(pdf_path)
    gui.show()
    app.exec()


def main():
    parser = argparse.ArgumentParser(
        description="Auto-crop PDF pages for better e-ink device viewing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_cropper.py document.pdf
  python pdf_cropper.py document.pdf --left 0.1 --right 0.1 --top 0.05 --bottom 0.05
  python pdf_cropper.py document.pdf -l 0.15 -r 0.1 -t 0.08 -b 0.12
  python pdf_cropper.py document.pdf --buffer 0.02
  python pdf_cropper.py document.pdf --footer-height 0.15

Crop values are percentages (0.0 to 1.0) of the page dimensions to remove.
For example, --left 0.1 removes 10% from the left margin.
Buffer adds extra space around auto-detected content (default 1%).
Footer-height controls how much of the bottom area to check for footer content.
        """
    )
    
    parser.add_argument("input_pdf", help="Input PDF file path")
    parser.add_argument("--gui", action="store_true", 
                       help="Launch GUI for interactive cropping")
    parser.add_argument("-l", "--left", type=float, 
                       help="Left margin to crop (0.0-1.0, default: auto-detect)")
    parser.add_argument("-r", "--right", type=float,
                       help="Right margin to crop (0.0-1.0, default: auto-detect)")
    parser.add_argument("-t", "--top", type=float,
                       help="Top margin to crop (0.0-1.0, default: auto-detect)")
    parser.add_argument("-b", "--bottom", type=float,
                       help="Bottom margin to crop (0.0-1.0, default: auto-detect)")
    parser.add_argument("--footer-height", type=float, default=0.1,
                       help="Height ratio to check for footer content (0.05-0.2, default: 0.1)")
    parser.add_argument("--buffer", type=float, default=0.01,
                       help="Buffer space around auto-detected content (0.0-0.1, default: 0.01)")
    parser.add_argument("-o", "--output", 
                       help="Output PDF path (default: input_filename-cropped.pdf)")
    parser.add_argument("--no-optimize", action="store_false", dest="optimize", default=True,
                       help="Disable optimization (compression) of the output PDF")
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_pdf)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.pdf':
        print(f"Error: Input file must be a PDF.")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}-cropped.pdf"
    
    # Validate crop parameters
    crop_params = [args.left, args.right, args.top, args.bottom]
    for param in crop_params:
        if param is not None and (param < 0 or param >= 1):
            print("Error: Crop values must be between 0.0 and 1.0")
            sys.exit(1)
    
    # Validate buffer parameter
    if args.buffer < 0 or args.buffer > 0.1:
        print("Error: Buffer value must be between 0.0 and 0.1")
        sys.exit(1)
    
    # Validate footer height parameter
    if args.footer_height < 0.05 or args.footer_height > 0.2:
        print("Error: Footer height must be between 0.05 and 0.2")
        sys.exit(1)
    
    # Launch GUI if requested
    if args.gui:
        run_gui(str(input_path))
        return
    
    try:
        print(f"Processing: {input_path}")
        print(f"Output will be saved as: {output_path}")
        
        crop_pdf(str(input_path), str(output_path), 
                args.left, args.top, args.right, args.bottom, args.buffer, args.footer_height, args.optimize)
        
        print("Done! Your PDF has been cropped and optimized for e-ink viewing.")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
