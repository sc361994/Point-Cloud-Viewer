import sys
import os
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTreeView, QLabel, 
                             QFileDialog, QSplitter, QFrame, QColorDialog, 
                             QSlider, QScrollArea)
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtCore import QDir, Qt

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MeshExplorer(QMainWindow):
    def __init__(self, startup_file=None):
        super().__init__()
        self.setWindowTitle("CAD Point Cloud Explorer Pro")
        self.resize(1400, 900)
        
        # Set Window Icon
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- SIDEBAR ---
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.left_container = QWidget()
        self.left_layout = QVBoxLayout(self.left_container)
        
        self.browse_btn = QPushButton("📁 Choose Base Folder")
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.clicked.connect(self.browse_folder)
        
        self.path_label = QLabel("No folder selected")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("font-size: 10px; color: gray;")

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Files)
        self.model.setNameFilters(["*.ply"])
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        for i in range(1, 4): self.tree.hideColumn(i)
        self.tree.clicked.connect(self.on_file_selected)

        self.slider_label = QLabel("<b>Downsampling: 1/1</b>")
        self.downsample_slider = QSlider(Qt.Orientation.Horizontal)
        self.downsample_slider.setRange(1, 50)
        self.downsample_slider.valueChanged.connect(self.refresh_view)
        
        self.bg_color_btn = QPushButton("🎨 Background Color")
        self.pc_color_btn = QPushButton("🔵 Point Color")
        self.bg_color_btn.clicked.connect(self.choose_bg_color)
        self.pc_color_btn.clicked.connect(self.choose_pc_color)
        
        self.screenshot_btn = QPushButton("📸 Save Screenshot")
        self.screenshot_btn.setStyleSheet("background-color: #2c3e50; color: white;")
        self.screenshot_btn.clicked.connect(self.take_screenshot)

        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)

        self.left_layout.addWidget(self.browse_btn)
        self.left_layout.addWidget(self.path_label)
        self.left_layout.addWidget(self.tree, 1)
        self.left_layout.addWidget(self.slider_label)
        self.left_layout.addWidget(self.downsample_slider)
        self.left_layout.addWidget(self.bg_color_btn)
        self.left_layout.addWidget(self.pc_color_btn)
        self.left_layout.addWidget(self.screenshot_btn)
        self.left_layout.addWidget(self.status_label)
        self.sidebar_scroll.setWidget(self.left_container)

        # --- VIEWER ---
        self.plotter = QtInteractor(self)
        self.plotter.set_background("white")
        
        self.splitter.addWidget(self.sidebar_scroll)
        self.splitter.addWidget(self.plotter.interactor)
        self.splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(self.splitter)

        self.current_mesh = None
        self.pc_color = "#1f77b4"

        # --- HANDLE STARTUP FILE (Open With...) ---
        if startup_file and os.path.isfile(startup_file):
            self.load_mesh(startup_file)
            # Set the tree to the folder of the opened file
            folder = os.path.dirname(startup_file)
            self.path_label.setText(folder)
            self.tree.setRootIndex(self.model.setRootPath(folder))

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.path_label.setText(folder)
            self.tree.setRootIndex(self.model.setRootPath(folder))

    def choose_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid(): self.plotter.set_background(color.name())

    def choose_pc_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.pc_color = color.name()
            self.refresh_view()

    def take_screenshot(self):
        if self.current_mesh:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save PNG", "", "PNG Files (*.png)")
            if file_path: self.plotter.screenshot(file_path)

    def on_file_selected(self, index):
        path = self.model.filePath(index)
        if path.lower().endswith(".ply"): self.load_mesh(path)

    def load_mesh(self, path):
        try:
            self.status_label.setText(f"Loading: {os.path.basename(path)}")
            QApplication.processEvents()
            self.current_mesh = pv.read(path)
            self.refresh_view()
            self.plotter.reset_camera()
        except Exception as e:
            self.status_label.setText(f"Error: {e}")

    def refresh_view(self):
        if self.current_mesh is None: return
        self.plotter.clear()
        stride = self.downsample_slider.value()
        self.slider_label.setText(f"<b>Downsampling: 1/{stride}</b>")
        display_mesh = self.current_mesh.extract_points(range(0, self.current_mesh.n_points, stride))
        self.plotter.add_mesh(display_mesh, color=self.pc_color, point_size=2.0, render_points_as_spheres=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check for arguments (Open With...)
    startup_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    window = MeshExplorer(startup_file=startup_path)
    window.show()
    sys.exit(app.exec())