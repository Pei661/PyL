import sys
import os
import json
import requests
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QComboBox, QListWidget, QMessageBox, QDialog, QLineEdit, QGridLayout, QRadioButton, QButtonGroup, QAction, QToolBar, QToolButton, QListWidgetItem
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# 加载语言文件
def load_language(lang_code):
    try:
        with open(f"languages/{lang_code}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Language file 'languages/{lang_code}.json' not found. Using default language.")
        return load_language("english")

# 加载已安装版本和账户
def load_installed_data():
    try:
        with open("versions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"versions": [], "accounts": []}

# 保存已安装版本和账户
def save_installed_data(data):
    with open("versions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# 获取 Minecraft 版本列表
def get_minecraft_versions():
    url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        versions = [entry["id"] for entry in data["versions"]]
        return versions
    else:
        QMessageBox.critical(None, "Error", "Failed to fetch Minecraft versions.")
        return []

# 下载 Minecraft 版本
def download_minecraft_version(version):
    url = f"https://launchermeta.mojang.com/mc/game/version_manifest.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for entry in data["versions"]:
            if entry["id"] == version:
                client_url = entry["url"]
                break
        else:
            QMessageBox.critical(None, "Error", f"Version {version} not found.")
            return None

        response = requests.get(client_url)
        if response.status_code == 200:
            return response.json()["downloads"]["client"]["url"]
        else:
            QMessageBox.critical(None, "Error", "Failed to fetch version details.")
            return None
    else:
        QMessageBox.critical(None, "Error", "Failed to fetch version manifest.")
        return None

# 下载并安装 Minecraft 版本
def install_minecraft_version(version, install_type, display_name):
    client_url = download_minecraft_version(version)
    if not client_url:
        return False

    response = requests.get(client_url, stream=True)
    if response.status_code == 200:
        version_dir = os.path.join(".minecraft", "versions", version)
        os.makedirs(version_dir, exist_ok=True)

        with open(os.path.join(version_dir, f"{version}.jar"), "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)

        # 创建版本配置文件
        version_config = {
            "name": version,
            "type": install_type,
            "displayName": display_name
        }
        with open(os.path.join(version_dir, "version.json"), "w", encoding="utf-8") as f:
            json.dump(version_config, f, indent=4)

        QMessageBox.information(None, "Success", f"Installed {display_name} ({install_type}) successfully.")
        return True
    else:
        QMessageBox.critical(None, "Error", "Failed to download Minecraft version.")
        return False

# 启动 Minecraft
def launch_minecraft(version, install_type, account_name):
    try:
        version_dir = os.path.join(".minecraft", "versions", version)
        if not os.path.exists(version_dir):
            QMessageBox.critical(None, "Error", f"Version {version} not found.")
            return

        # 启动命令
        command = [
            "java", "-Xmx2G", "-Xms2G", "-jar", os.path.join(version_dir, f"{version}.jar"), "nogui",
            "--username", account_name
        ]
        subprocess.run(command)
        QMessageBox.information(None, "Success", f"Minecraft {version} has been launched!")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to launch Minecraft: {e}")

# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = load_language("english")  # 默认语言为英文
        self.data = load_installed_data()
        self.setWindowTitle(self.language["welcome_message"])
        self.resize(800, 600)  # 设置初始窗口大小

        # 设置背景图片
        bg_label = QLabel(self)
        pixmap = QPixmap("images/bg.png")
        bg_label.setPixmap(pixmap)
        bg_label.setGeometry(0, 0, 800, 600)

        # 顶部欢迎文字
        self.welcome_label = QLabel(self.language["welcome_message"], self)
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setGeometry(50, 20, 700, 50)

        # 创建工具栏
        self.toolbar = self.addToolBar("Toolbar")

        # 下载版本按钮
        self.download_button = QAction(self.language["download_version"], self)
        self.download_button.triggered.connect(self.open_download_window)
        self.toolbar.addAction(self.download_button)

        # 启动 MC 按钮
        self.launch_button = QAction(self.language["launch_mc"], self)
        self.launch_button.triggered.connect(self.open_version_selector)
        self.toolbar.addAction(self.launch_button)

        # 创建离线账户按钮
        self.create_account_button = QAction(self.language["create_account"], self)
        self.create_account_button.triggered.connect(self.open_account_creator)
        self.toolbar.addAction(self.create_account_button)

        # 管理账号按钮
        self.manage_accounts_button = QAction(self.language["manage_accounts"], self)
        self.manage_accounts_button.triggered.connect(self.open_account_manager)
        self.toolbar.addAction(self.manage_accounts_button)

        # 管理版本按钮
        self.manage_versions_button = QAction(self.language["manage_versions"], self)
        self.manage_versions_button.triggered.connect(self.open_version_manager)
        self.toolbar.addAction(self.manage_versions_button)

        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Chinese"])
        self.language_combo.currentTextChanged.connect(self.change_language)
        self.toolbar.addWidget(self.language_combo)

        # 检查是否有已安装版本
        if not self.data["versions"]:
            self.launch_button.setEnabled(False)

    def change_language(self, lang):
        if lang == "English":
            self.language = load_language("english")
        elif lang == "Chinese":
            self.language = load_language("chinese")
        self.update_ui_language()

    def update_ui_language(self):
        self.setWindowTitle(self.language["welcome_message"])
        self.welcome_label.setText(self.language["welcome_message"])
        self.download_button.setText(self.language["download_version"])
        self.launch_button.setText(self.language["launch_mc"])
        self.create_account_button.setText(self.language["create_account"])
        self.manage_accounts_button.setText(self.language["manage_accounts"])
        self.manage_versions_button.setText(self.language["manage_versions"])

    def open_download_window(self):
        DownloadWindow(self).exec_()

    def open_version_selector(self):
        if not self.data["versions"]:
            QMessageBox.information(self, "Info", self.language["no_versions_installed"])
            return
        VersionSelector(self).exec_()

    def open_account_creator(self):
        AccountCreator(self).exec_()

    def open_account_manager(self):
        AccountManager(self).exec_()

    def open_version_manager(self):
        VersionManager(self).exec_()

# 下载版本窗口
class DownloadWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.parent().language["download_version"])
        self.setFixedSize(400, 400)

        layout = QGridLayout()

        # 获取版本列表
        self.versions = get_minecraft_versions()

        # 版本列表
        self.list_widget = QListWidget()
        self.list_widget.addItems(self.versions)
        layout.addWidget(self.list_widget, 0, 0, 1, 2)

        # 重命名版本
        self.rename_label = QLabel(self.parent().language["rename_version"])
        self.rename_input = QLineEdit(self)
        layout.addWidget(self.rename_label, 1, 0)
        layout.addWidget(self.rename_input, 1, 1)

        # 安装类型单选按钮
        self.button_group = QButtonGroup(self)
        self.original_radio = QRadioButton(self.parent().language["original"])
        self.forge_radio = QRadioButton(self.parent().language["forge"])
        self.fabric_radio = QRadioButton(self.parent().language["fabric"])
        self.quilt_radio = QRadioButton(self.parent().language["quilt"])
        self.button_group.addButton(self.original_radio)
        self.button_group.addButton(self.forge_radio)
        self.button_group.addButton(self.fabric_radio)
        self.button_group.addButton(self.quilt_radio)
        layout.addWidget(self.original_radio, 2, 0)
        layout.addWidget(self.forge_radio, 2, 1)
        layout.addWidget(self.fabric_radio, 3, 0)
        layout.addWidget(self.quilt_radio, 3, 1)

        # 安装按钮
        install_button = QPushButton(self.parent().language["install"])
        install_button.clicked.connect(self.install_version)
        layout.addWidget(install_button, 4, 0, 1, 2)

        self.setLayout(layout)

    def install_version(self):
        selected_version = self.list_widget.currentItem().text()
        display_name = self.rename_input.text() or selected_version
        install_type = ""
        if self.original_radio.isChecked():
            install_type = "original"
        elif self.forge_radio.isChecked():
            install_type = "forge"
        elif self.fabric_radio.isChecked():
            install_type = "fabric"
        elif self.quilt_radio.isChecked():
            install_type = "quilt"

        # 安装 Minecraft 版本
        if install_minecraft_version(selected_version, install_type, display_name):
            # 保存已安装版本
            self.parent().data["versions"].append({"name": selected_version, "display_name": display_name, "type": install_type})
            save_installed_data(self.parent().data)
            self.parent().launch_button.setEnabled(True)
            QMessageBox.information(self, "Success", f"Installed {display_name} ({install_type}) successfully.")
        self.close()

# 版本选择窗口
class VersionSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.parent().language["select_version"])
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # 已安装版本列表
        self.list_widget = QListWidget()
        for version in self.parent().data["versions"]:
            item = QListWidgetItem(f"{version['display_name']} [{version['type']}]")
            item.setData(Qt.UserRole, version)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # 启动按钮
        launch_button = QPushButton(self.parent().language["launch_mc"])
        launch_button.clicked.connect(self.launch_mc)
        layout.addWidget(launch_button)

        # 打开文件夹按钮
        open_folder_button = QPushButton(self.parent().language["open_folder"])
        open_folder_button.clicked.connect(self.open_folder)
        layout.addWidget(open_folder_button)

        # 删除版本按钮
        delete_button = QPushButton(self.parent().language["delete_version"])
        delete_button.clicked.connect(self.delete_version)
        layout.addWidget(delete_button)

        self.setLayout(layout)

    def launch_mc(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Info", "Please select a version to launch.")
            return

        version_data = selected_item.data(Qt.UserRole)
        selected_version = version_data["name"]
        install_type = version_data["type"]

        # 获取账户名称
        account_name = self.parent().data["accounts"][0]["name"] if self.parent().data["accounts"] else "offline_user"

        # 启动 Minecraft
        launch_minecraft(selected_version, install_type, account_name)

    def open_folder(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Info", "Please select a version to open its folder.")
            return

        version_data = selected_item.data(Qt.UserRole)
        selected_version = version_data["name"]

        # 打开版本文件夹
        folder_path = os.path.join(".minecraft", "versions", selected_version)
        os.startfile(folder_path)

    def delete_version(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Info", "Please select a version to delete.")
            return

        confirm = QMessageBox.question(self, "Confirm", self.parent().language["confirm_delete"])
        if confirm == QMessageBox.Yes:
            version_data = selected_item.data(Qt.UserRole)
            selected_version = version_data["name"]
            self.parent().data["versions"] = [v for v in self.parent().data["versions"] if v["name"] != selected_version]
            save_installed_data(self.parent().data)
            self.list_widget.takeItem(self.list_widget.row(selected_item))
            QMessageBox.information(self, "Success", "Version deleted successfully.")

# 离线账户创建窗口
class AccountCreator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.parent().language["create_account"])
        self.setFixedSize(300, 200)

        layout = QGridLayout()

        # 账户名称输入
        self.name_label = QLabel(self.parent().language["account_name"])
        self.name_input = QLineEdit(self)
        layout.addWidget(self.name_label, 0, 0)
        layout.addWidget(self.name_input, 0, 1)

        # 创建按钮
        create_button = QPushButton("Create")
        create_button.clicked.connect(self.create_account)
        layout.addWidget(create_button, 1, 0, 1, 2)

        self.setLayout(layout)

    def create_account(self):
        account_name = self.name_input.text()
        if not account_name:
            QMessageBox.warning(self, "Warning", "Please enter an account name.")
            return

        # 保存账户
        self.parent().data["accounts"].append({"name": account_name})
        save_installed_data(self.parent().data)
        QMessageBox.information(self, "Success", f"Account '{account_name}' created successfully.")
        self.close()

# 账号管理窗口
class AccountManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.parent().language["manage_accounts"])
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()

        # 已创建账户列表
        self.list_widget = QListWidget()
        for account in self.parent().data["accounts"]:
            item = QListWidgetItem(account["name"])
            item.setData(Qt.UserRole, account)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # 右键菜单
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.setLayout(layout)

    def show_context_menu(self, position):
        menu = QMenu(self)
        edit_action = QAction(self.parent().language["edit"], self)
        delete_action = QAction(self.parent().language["delete"], self)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        action = menu.exec_(self.list_widget.viewport().mapToGlobal(position))

        if action == edit_action:
            self.edit_account()
        elif action == delete_action:
            self.delete_account()

    def edit_account(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Info", "Please select an account to edit.")
            return

        account_data = selected_item.data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(self, "Edit Account", "Enter new account name:", text=account_data["name"])
        if ok and new_name:
            account_data["name"] = new_name
            selected_item.setText(new_name)
            save_installed_data(self.parent().data)
            QMessageBox.information(self, "Success", f"Account name changed to '{new_name}'.")

    def delete_account(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Info", "Please select an account to delete.")
            return

        confirm = QMessageBox.question(self, "Confirm", "Are you sure you want to delete this account?")
        if confirm == QMessageBox.Yes:
            account_data = selected_item.data(Qt.UserRole)
            self.parent().data["accounts"] = [a for a in self.parent().data["accounts"] if a["name"] != account_data["name"]]
            save_installed_data(self.parent().data)
            self.list_widget.takeItem(self.list_widget.row(selected_item))
            QMessageBox.information(self, "Success", "Account deleted successfully.")

# 版本管理窗口
class VersionManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.parent().language["manage_versions"])
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # 已安装版本列表
        self.list_widget = QListWidget()
        for version in self.parent().data["versions"]:
            item = QListWidgetItem(f"{version['display_name']} [{version['type']}]")
            item.setData(Qt.UserRole, version)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # 右键菜单
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.setLayout(layout)

    def show_context_menu(self, position):
        menu = QMenu(self)
        open_folder_action = QAction(self.parent().language["open_folder"], self)
        delete_action = QAction(self.parent().language["delete_version"], self)
        menu.addAction(open_folder_action)
        menu.addAction(delete_action)
        action = menu.exec_(self.list_widget.viewport().mapToGlobal(position))

        if action == open_folder_action:
            self.open_folder()
        elif action == delete_action:
            self.delete_version()

    def open_folder(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Info", "Please select a version to open its folder.")
            return

        version_data = selected_item.data(Qt.UserRole)
        selected_version = version_data["name"]

        # 打开版本文件夹
        folder_path = os.path.join(".minecraft", "versions", selected_version)
        os.startfile(folder_path)

    def delete_version(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Info", "Please select a version to delete.")
            return

        confirm = QMessageBox.question(self, "Confirm", self.parent().language["confirm_delete"])
        if confirm == QMessageBox.Yes:
            version_data = selected_item.data(Qt.UserRole)
            selected_version = version_data["name"]
            self.parent().data["versions"] = [v for v in self.parent().data["versions"] if v["name"] != selected_version]
            save_installed_data(self.parent().data)
            self.list_widget.takeItem(self.list_widget.row(selected_item))
            QMessageBox.information(self, "Success", "Version deleted successfully.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
