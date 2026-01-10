#!/usr/bin/env python3
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize

from models import ScaleModel, InstrumentModel
from modules.spelling import Spelling
from views.fretboard import FretboardView
from views.piano import PianoView
from views.tonnetz import TonnetzView
from views.polygon import PolygonView
from views.scale_selector import ScaleSelectorView
from views.main_window import MainWindow

def main():
    # A QApplication instance is necessary to create QWidgets and perform painting,
    # even if we don't start the event loop with exec().
    app = QApplication(sys.argv)

    # Initialize Models
    scale_model = ScaleModel()
    instrument_model = InstrumentModel()
    spelling = Spelling(scale_model)
    main_window = MainWindow()

    if len(sys.argv) > 1:
        try:
            scale_shape = int(sys.argv[1])
            print(f"Setting scale shape to: {scale_shape}")
            scale_model.set_shape(scale_shape)
            main_window.scale_model.set_shape(scale_shape)
        except ValueError:
            print(f"Ignoring invalid argument: {sys.argv[1]}")

    # Create output directory
    output_dir = "screenshots"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Configuration for views to render: (filename_prefix, ViewClass, Size)
    # Note: We instantiate views with the shared models.
    views_config = [
        ("main_window", main_window, QSize(1800, 400)),
        # ("fretboard", FretboardView(instrument_model, scale_model, spelling), QSize(1000, 300)),
        # ("piano", PianoView(scale_model, spelling), QSize(1000, 300)),
        # ("tonnetz", TonnetzView(scale_model, spelling), QSize(800, 600)),
        # ("polygon", PolygonView(scale_model, spelling), QSize(500, 500)),
        # ("scale_selector", ScaleSelectorView(scale_model, spelling), QSize(800, 80))
    ]

    print(f"Rendering {len(views_config)} views to '{output_dir}/'...")

    for name, widget, size in views_config:
        # Set the size of the widget. This determines the size of the output image.
        widget.resize(size)
        
        # grab() renders the widget into a QPixmap.
        # This works even if the widget is not visible on screen.
        pixmap = widget.grab()
        
        output_path = os.path.join(output_dir, f"{name}.png")
        pixmap.save(output_path)
        print(f"  Saved {output_path}")

    print("Done.")

if __name__ == "__main__":
    main()
