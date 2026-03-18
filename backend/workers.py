from PyQt6.QtCore import QThread, pyqtSignal
from .package_manager import PackageManager
from .managers import InventoryManager, Package, PackageSource

class SearchWorker(QThread):
    """Gelişmiş hibrit arama işçisi."""
    finished = pyqtSignal(list)

    def __init__(self, query, category=None):
        super().__init__()
        self.query = query
        self.category = category
        self.pm = PackageManager()
        self.im = InventoryManager()

    def run(self):
        raw_results = self.pm.search_packages(self.query, self.category)
        installed_pacman = self.im.get_installed_pacman_packages()
        installed_flatpaks = self.im.get_installed_flatpaks()
        
        final_packages = []
        
        # Depo sonuçlarını işle
        for res in raw_results:
            source_enum = PackageSource(res['source'])
            
            status = "available"
            if source_enum == PackageSource.PACMAN and res['name'] in installed_pacman:
                status = "installed"
            elif source_enum == PackageSource.FLATPAK and res['name'] in installed_flatpaks:
                status = "installed"
            
            pkg = Package(
                name=res['name'],
                display_name=res.get('display_name', res['name']),
                version=res['version'],
                description=res['description'],
                source=source_enum,
                status=status
            )
            final_packages.append(pkg)

        self.finished.emit(final_packages)