#!/usr/bin/env python3
import sys, os, traceback

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.portal=false;qt.qpa.services=false"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("arxis")
    app.setApplicationDisplayName("Arxis")
    app.setOrganizationName("arxis")
    app.setOrganizationDomain("arxis.local")
    app.setDesktopFileName("arxis")
    app.setFont(QFont("Segoe UI", 10))

    try:
        from ui.main_window import ArchPackageStore
        window = ArchPackageStore()
        window.show()
    except Exception:
        from PyQt6.QtWidgets import QMessageBox
        msg = traceback.format_exc()
        print(msg, file=sys.stderr)
        dlg = QMessageBox()
        dlg.setWindowTitle("Başlatma Hatası")
        dlg.setText("Arayüz modülleri yüklenemedi.")
        dlg.setDetailedText(msg)
        dlg.exec()
        sys.exit(1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()