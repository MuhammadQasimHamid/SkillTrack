
"""
SkillTrack GUI - PyQt6 version
Converted from a console interface to a tabbed PyQt6 application.

Exposes:
- Entity Management (add/view)
- Start Session
- End Session
- Reports (single entity or all in last 7 days)

This file replaces the previous CLI loop and uses functions from `logic.py`.
"""

import sys
import os
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QPushButton, QMessageBox,
    QComboBox, QTabWidget, QFormLayout, QDialog, QDialogButtonBox, QDateEdit, QSizePolicy, QStyle, QFileDialog,
    QSystemTrayIcon, QMenu, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QDate, QSettings, QSize, QPoint

# Matplotlib (optional) for plotting reports
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

# Optional pyqtgraph for interactive plots
try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except Exception:
    PG = None
    PYQTGRAPH_AVAILABLE = False

from logic import Entity, calculateTotalTime
from skilltrack.controller import (
    get_entities, create_entity, delete_entity, update_entity,
    get_started_sessions, start_entity_session, stop_session,
    get_completed_sessions, generate_report,
    register_user, login_user, logout_user, is_authenticated, current_user, list_users,
    get_goals, add_goal, update_goal, delete_goal,
    delete_session, recover_session
)
from PyQt6.QtGui import QAction, QIcon


class AddEntityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Entity")
        self.layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(["Skill", "Project"])
        self.desc_input = QLineEdit()
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Type:", self.type_input)
        self.layout.addRow("Description:", self.desc_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self):
        return self.name_input.text().strip(), self.type_input.currentText(), self.desc_input.text().strip()


class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Register')
        self.layout = QFormLayout(self)
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm = QLineEdit()
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addRow('Username:', self.username)
        self.layout.addRow('Password:', self.password)
        self.layout.addRow('Confirm:', self.password_confirm)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.on_accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def on_accept(self):
        user = self.username.text().strip()
        pwd = self.password.text()
        pwd2 = self.password_confirm.text()
        if not user:
            QMessageBox.warning(self, 'Validation', 'Username is required')
            return
        if not pwd:
            QMessageBox.warning(self, 'Validation', 'Password is required')
            return
        if pwd != pwd2:
            QMessageBox.warning(self, 'Validation', 'Passwords do not match')
            return
        ok = register_user(user, pwd)
        if not ok:
            QMessageBox.warning(self, 'Exists', 'User already exists')
            return
        # auto-login after successful registration
        from skilltrack.controller import login_user
        login_user(user, pwd)
        QMessageBox.information(self, 'Registered', f'User {user} created and logged in')
        self.accept()


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Login')
        self.layout = QFormLayout(self)
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addRow('Username:', self.username)
        self.layout.addRow('Password:', self.password)

        self.buttons = QDialogButtonBox()
        self.login_btn = self.buttons.addButton('Login', QDialogButtonBox.ButtonRole.AcceptRole)
        self.register_btn = self.buttons.addButton('Register', QDialogButtonBox.ButtonRole.ActionRole)
        self.cancel_btn = self.buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.login_btn.clicked.connect(self.on_login)
        self.register_btn.clicked.connect(self.on_register)
        self.cancel_btn.clicked.connect(self.reject)
        self.layout.addRow(self.buttons)

    def on_login(self):
        user = self.username.text().strip()
        pwd = self.password.text()
        if not user or not pwd:
            QMessageBox.warning(self, 'Validation', 'Both fields are required')
            return
        ok = login_user(user, pwd)
        if not ok:
            QMessageBox.warning(self, 'Login Failed', 'Invalid username or password')
            return
        QMessageBox.information(self, 'Welcome', f'Logged in as {user}')
        self.accept()

    def on_register(self):
        dlg = RegisterDialog(self)
        dlg.exec()


class GoalDialog(QDialog):
    def __init__(self, parent=None, goal=None):
        super().__init__(parent)
        self.setWindowTitle("Add Goal" if not goal else "Edit Goal")
        self.layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.target_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(["Incomplete", "Completed"])
        
        if goal:
            self.name_input.setText(goal.name)
            self.target_input.setText(str(goal.targetHours))
            self.status_input.setCurrentText(goal.status)
        
        self.layout.addRow("Milestone Name:", self.name_input)
        self.layout.addRow("Target Hours:", self.target_input)
        if goal:
            self.layout.addRow("Status:", self.status_input)
            
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_data(self):
        name = self.name_input.text().strip()
        try:
            target = float(self.target_input.text())
        except ValueError:
            target = 0.0
        status = self.status_input.currentText()
        return name, target, status


class EditEntityDialog(AddEntityDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Entity")

    def set_data(self, name, type_, desc):
        self.name_input.setText(name)
        idx = self.type_input.findText(type_)
        if idx >= 0:
            self.type_input.setCurrentIndex(idx)
        self.desc_input.setText(desc)


class TrashBinDialog(QDialog):
    def __init__(self, entities, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trash Bin - Deleted Sessions")
        self.resize(500, 400)
        self.entities = entities
        self.layout = QVBoxLayout(self)
        
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.layout.addWidget(self.list)
        
        self.refresh_list()
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def refresh_list(self):
        self.list.clear()
        try:
            all_sessions = get_completed_sessions(include_deleted=True)
            deleted = [s for s in all_sessions if s.is_deleted == 1]
        except Exception:
            deleted = []
        
        for s in sorted(deleted, key=lambda x: x.startTime, reverse=True):
            ent = next((e for e in self.entities if e.id == s.entityId), None)
            name = ent.name if ent else f"Entity {s.entityId}"
            start_str = s.startTime.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create a widget for the row
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 2, 5, 2)
            
            info = QLabel(f"[{s.id}] {name} — {start_str}")
            info.setStyleSheet("font-size: 11px;")
            
            restore_btn = QPushButton("Restore")
            restore_btn.setFixedWidth(70)
            restore_btn.setStyleSheet("background-color: #d1e7dd; border: 1px solid #badbcc; border-radius: 4px;")
            restore_btn.clicked.connect(lambda checked, sess_id=s.id: self.on_restore_item(sess_id))
            
            item_layout.addWidget(info)
            item_layout.addStretch()
            item_layout.addWidget(restore_btn)
            
            item = QListWidgetItem(self.list)
            item.setSizeHint(item_widget.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, item_widget)

    def on_restore_item(self, session_id):
        recover_session(session_id)
        # QMessageBox.information(self, "Restored", f"Session {session_id} has been restored.")
        self.refresh_list()
        if self.parent():
            self.parent().load_sessions()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkillTrack - Compact")
        # Load saved window geometry
        self.settings = QSettings("SkillTrack", "SkillTrackGUI")
        self.resize(self.settings.value("size", QSize(900, 600)))
        self.move(self.settings.value("pos", QPoint(50, 50)))
        self.setMinimumSize(100, 100)
        
        # Set window icon
        for icon_path in ["stopwatch.ico", "stopwatch.png"]:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # five tabs: Timers, Entities, Sessions, Reports, Goals
        self.timers_tab = QWidget()
        self.entities_tab = QWidget()
        self.sessions_tab = QWidget()
        self.report_tab = QWidget()
        self.goals_tab = QWidget()

        self.tabs.addTab(self.timers_tab, "Timers")
        self.tabs.addTab(self.entities_tab, "Entities")
        self.tabs.addTab(self.sessions_tab, "Sessions")
        self.tabs.addTab(self.report_tab, "Reports")
        self.tabs.addTab(self.goals_tab, "Goals")

        self._build_timers_tab()
        self._build_entities_tab()
        self._build_sessions_tab()
        self._build_report_tab()
        self._build_goals_tab()

        # Start a UI timer to refresh elapsed timers every second
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.load_timers)
        self.ui_timer.start(1000)

        # Account menu and status
        self._build_account_menu()
        self.update_user_ui()

        # System Tray initialization
        self.setup_system_tray()

        self.refresh_all()

    def _build_account_menu(self):
        menubar = self.menuBar()
        account_menu = menubar.addMenu('Account')
        self.logout_action = QAction('Logout', self)
        self.logout_action.triggered.connect(self.on_logout)
        account_menu.addAction(self.logout_action)

    def update_user_ui(self):
        # reflect current user in window title and status bar
        user = current_user()
        if user:
            self.setWindowTitle(f"SkillTrack - Compact (User: {user})")
            self.statusBar().showMessage(f"Logged in as {user}")
            self.logout_action.setEnabled(True)
            if hasattr(self, 'logout_timer_btn'):
                self.logout_timer_btn.setEnabled(True)
        else:
            self.setWindowTitle("SkillTrack - Compact")
            self.statusBar().clearMessage()
            self.logout_action.setEnabled(False)
            if hasattr(self, 'logout_timer_btn'):
                self.logout_timer_btn.setEnabled(False)

    def on_logout(self):
        confirm = QMessageBox.question(self, 'Logout', 'Logout and switch user?')
        if confirm == QMessageBox.StandardButton.Yes:
            logout_user()
            self.update_user_ui()
            # prompt for login again
            dlg = LoginDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                # user cancelled login → exit app
                QApplication.instance().quit()
            else:
                self.update_user_ui()

    def _build_timers_tab(self):
        layout = QVBoxLayout()
        # Top controls: Switch User and Logout buttons
        top_controls = QHBoxLayout()
        self.switch_user_btn = QPushButton('Switch User')
        self.switch_user_btn.setToolTip('Switch to another user (login)')
        self.switch_user_btn.clicked.connect(self.on_switch_user)
        self.logout_timer_btn = QPushButton('Logout')
        self.logout_timer_btn.setToolTip('Logout current user')
        self.logout_timer_btn.clicked.connect(self.on_logout)
        top_controls.addWidget(self.switch_user_btn)
        top_controls.addStretch()
        top_controls.addWidget(self.logout_timer_btn)
        layout.addLayout(top_controls)

        # timer_list will show each entity with a Start/Stop button and an elapsed label
        self.timer_list = QListWidget()
        layout.addWidget(self.timer_list)
        self.timers_tab.setLayout(layout)

    def on_switch_user(self):
        dlg = LoginDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.update_user_ui()
            self.refresh_all()

    def setup_system_tray(self):
        # Create the tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use stopwatch.ico or stopwatch.png if they exist
        icon_set = False
        for icon_path in ["stopwatch.ico", "stopwatch.png"]:
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
                icon_set = True
                break
        if not icon_set:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        # Create the tray menu
        self.tray_menu = QMenu(self)
        
        self.restore_action = QAction("Restore", self)
        self.restore_action.triggered.connect(self.showNormal)
        self.restore_action.triggered.connect(self.activateWindow)
        
        self.quit_action = QAction("Exit", self)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        
        # dynamic_timers_menu will be populated in update_tray_menu
        self.tray_menu.addAction(self.restore_action)
        self.tray_menu.addSeparator()
        # placeholder for timers will be between separators
        self.tray_menu.addAction(self.quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def update_tray_menu(self):
        # Clear existing dynamic timer actions
        # We'll recreate the menu structure to keep it simple
        self.tray_menu.clear()
        self.tray_menu.addAction(self.restore_action)
        self.tray_menu.addSeparator()
        
        now = datetime.now()
        active_found = False
        if hasattr(self, 'started') and self.started:
            for s in self.started:
                # find entity name
                entity = next((e for e in self.entities if e.id == s.entityId), None)
                if entity:
                    active_found = True
                    elapsed = int((now - s.startTime).total_seconds())
                    h = elapsed // 3600
                    m = (elapsed % 3600) // 60
                    sec = elapsed % 60
                    timer_text = f"● {entity.name}: {h:02d}:{m:02d}:{sec:02d}"
                    timer_action = QAction(timer_text, self)
                    # Clicking a timer action could restore the window
                    timer_action.triggered.connect(self.showNormal)
                    timer_action.triggered.connect(self.activateWindow)
                    self.tray_menu.addAction(timer_action)
        
        if not active_found:
            no_timers_action = QAction("No running timers", self)
            no_timers_action.setEnabled(False)
            self.tray_menu.addAction(no_timers_action)
            self.tray_icon.setToolTip("SkillTrack: No running timers")
        else:
            # Build tooltip string for running timers
            tooltips = ["SkillTrack: Running Timers"]
            for s in self.started:
                entity = next((e for e in self.entities if e.id == s.entityId), None)
                if entity:
                    elapsed = int((now - s.startTime).total_seconds())
                    h = elapsed // 3600
                    m = (elapsed % 3600) // 60
                    sec = elapsed % 60
                    tooltips.append(f"• {entity.name}: {h:02d}:{m:02d}:{sec:02d}")
            self.tray_icon.setToolTip("\n".join(tooltips))
            
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)

    def closeEvent(self, event):
        # Save window geometry
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        
        if self.tray_icon.isVisible():
            # Hide to tray instead of closing
            self.hide()
            event.ignore()
        else:
            event.accept()

    def _build_entities_tab(self):
        layout = QVBoxLayout()
        self.entity_list = QListWidget()
        controls = QHBoxLayout()
        self.add_entity_btn = QPushButton("Add")
        self.add_entity_btn.clicked.connect(self.add_entity)
        self.edit_entity_btn = QPushButton("Edit")
        self.edit_entity_btn.clicked.connect(self.edit_selected_entity)
        self.delete_entity_btn = QPushButton("Delete")
        self.delete_entity_btn.clicked.connect(self.delete_selected_entity)
        controls.addWidget(self.add_entity_btn)
        controls.addWidget(self.edit_entity_btn)
        controls.addWidget(self.delete_entity_btn)
        layout.addLayout(controls)
        layout.addWidget(self.entity_list)
        self.entities_tab.setLayout(layout)

    def _build_sessions_tab(self):
        layout = QVBoxLayout()
        top = QHBoxLayout()
        # entity filter for sessions
        self.sessions_entity_combo = QComboBox()
        self.sessions_entity_combo.addItem('-- All Entities --', userData=None)
        self.sessions_entity_combo.currentIndexChanged.connect(self.load_sessions)
        self.sessions_refresh_btn = QPushButton('Refresh')
        self.sessions_refresh_btn.clicked.connect(self.load_sessions)
        top.addWidget(self.sessions_entity_combo)
        top.addWidget(self.sessions_refresh_btn)
        layout.addLayout(top)

        # sessions list
        self.sessions_list = QListWidget()
        self.sessions_list.itemDoubleClicked.connect(self.show_session_details)
        layout.addWidget(self.sessions_list)

        # Compact bottom row for session actions
        bottom_row = QHBoxLayout()
        
        # note about content
        note = QLabel('Double-click for details')
        note.setStyleSheet('color:#666;font-size:10px;')
        bottom_row.addWidget(note)
        
        bottom_row.addStretch()

        self.delete_session_btn = QPushButton("Delete")
        self.delete_session_btn.setToolTip("Delete selected session")
        self.delete_session_btn.setFixedWidth(80)
        self.delete_session_btn.clicked.connect(self.on_delete_session)
        
        self.trash_btn = QPushButton("Trash")
        self.trash_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.trash_btn.setToolTip("View deleted sessions")
        self.trash_btn.setFixedWidth(80)
        self.trash_btn.clicked.connect(self.on_open_trash)
        
        bottom_row.addWidget(self.delete_session_btn)
        bottom_row.addWidget(self.trash_btn)
        layout.addLayout(bottom_row)

        self.sessions_tab.setLayout(layout)

    def _build_report_tab(self):
        layout = QVBoxLayout()
        controls = QHBoxLayout()
        self.report_start_date = QDate.currentDate().addDays(-7)
        self.report_end_date = QDate.currentDate()
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(self.report_start_date)
        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(self.report_end_date)

        # Entity filter (All or specific)
        self.entity_filter_combo = QComboBox(self)
        self.entity_filter_combo.addItem('-- All Entities --', userData=None)

        self.generate_report_btn = QPushButton('Generate')
        self.generate_report_btn.clicked.connect(self.load_reports)

        # Button to open full report window (graph + controls) will be placed at bottom next to the note
        self.full_report_btn = QPushButton('Full Report')
        self.full_report_btn.clicked.connect(self.open_full_report)

        # Calendar emoji labels for date edits (clear calendar icon)
        start_icon_lbl = QLabel('📅')
        start_icon_lbl.setToolTip('Start Date')
        start_icon_lbl.setStyleSheet('font-size:14px;')
        start_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_icon_lbl.setFixedWidth(22)
        self.start_date_edit.setToolTip('Start Date')
        end_icon_lbl = QLabel('📅')
        end_icon_lbl.setToolTip('End Date')
        end_icon_lbl.setStyleSheet('font-size:14px;')
        end_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        end_icon_lbl.setFixedWidth(22)
        self.end_date_edit.setToolTip('End Date')

        controls.addWidget(start_icon_lbl)
        controls.addWidget(self.start_date_edit)
        controls.addWidget(end_icon_lbl)
        controls.addWidget(self.end_date_edit)
        controls.addWidget(self.entity_filter_combo)
        controls.addWidget(self.generate_report_btn)

        self.report_out = QTextEdit()
        self.report_out.setReadOnly(True)

        layout.addLayout(controls)
        layout.addWidget(self.report_out)

        # bottom area: note + Full Report button on the right
        bottom = QHBoxLayout()
        note = QLabel('Graph available in Full Report window')
        note.setStyleSheet('color:#888;font-size:11px;')
        bottom.addWidget(note)
        bottom.addStretch()
        bottom.addWidget(self.full_report_btn)
        layout.addLayout(bottom)

        self.report_tab.setLayout(layout)

    def refresh_all(self):
        self.load_entities()
        self.load_timers()
        self.load_sessions()
        self.load_reports()
        self.load_goals()

    def load_entities(self):
        try:
            self.entities = get_entities()
        except Exception:
            self.entities = []
        
        self.entity_list.clear()
        
        # 1. Reports tab filter
        self.entity_filter_combo.clear()
        self.entity_filter_combo.addItem('-- All Entities --', userData=None)
        
        # 2. Sessions tab filter
        if hasattr(self, 'sessions_entity_combo'):
            self.sessions_entity_combo.clear()
            self.sessions_entity_combo.addItem('-- All Entities --', userData=None)
            
        # 3. Goals tab filter
        if hasattr(self, 'goals_entity_combo'):
            self.goals_entity_combo.clear()
            self.goals_entity_combo.addItem('-- Select Entity --', userData=None)
            
        for e in self.entities:
            self.entity_list.addItem(f"{e.id} - {e.name} ({e.type})")
            
            # Populate combos
            self.entity_filter_combo.addItem(f"{e.id} - {e.name}", userData=e.id)
            
            if hasattr(self, 'sessions_entity_combo'):
                self.sessions_entity_combo.addItem(f"{e.id} - {e.name}", userData=e.id)
                
            if hasattr(self, 'goals_entity_combo'):
                self.goals_entity_combo.addItem(f"{e.id} - {e.name}", userData=e.id)

    def add_entity(self):
        dlg = AddEntityDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, typ, desc = dlg.get_data()
            if not name:
                QMessageBox.warning(self, "Validation", "Name is required")
                return
            entity = create_entity(name, typ, desc)
            QMessageBox.information(self, "Saved", "Entity added")
            self.refresh_all()

    def delete_selected_entity(self):
        row = self.entity_list.currentRow()
        if row < 0:
            return
        entity = self.entities[row]
        confirm = QMessageBox.question(self, "Confirm", f"Delete entity '{entity.name}'? This will not remove historical sessions.")
        if confirm == QMessageBox.StandardButton.Yes:
            success = delete_entity(entity.id)
            if success:
                QMessageBox.information(self, "Deleted", "Entity deleted")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete entity")
            self.refresh_all()

    def edit_selected_entity(self):
        row = self.entity_list.currentRow()
        if row < 0:
            return
        entity = self.entities[row]
        dlg = EditEntityDialog(self)
        dlg.set_data(entity.name, entity.type, entity.description)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, typ, desc = dlg.get_data()
            if not name:
                QMessageBox.warning(self, "Validation", "Name is required")
                return
            success = update_entity(entity.id, name, typ, desc)
            if success:
                QMessageBox.information(self, "Saved", "Entity updated")
                self.refresh_all()
            else:
                QMessageBox.warning(self, "Error", "Failed to update entity")

    def load_timers(self):
        # Load started sessions to determine active timers
        try:
            self.started = get_started_sessions()
        except Exception:
            self.started = []

        self.timer_list.clear()
        now = datetime.now()
        # show running entities first
        entities_sorted = sorted(self.entities, key=lambda ee: any(s.entityId == ee.id for s in self.started), reverse=True)
        for e in entities_sorted:
            item = QListWidgetItem()
            widget = QWidget()
            h = QHBoxLayout()
            label = QLabel(e.name)
            label.setStyleSheet('font-weight:bold')

            elapsed_label = QLabel('')
            elapsed_label.setStyleSheet('color:#666;font-size:11px;')

            btn = QPushButton()
            style = QApplication.style()
            active = next((s for s in self.started if s.entityId == e.id), None)
            if active and active.startTime:
                btn.setText('Stop')
                btn.setObjectName('stopBtn')
                stop_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaStop)
                btn.setIcon(stop_icon)
                btn.setToolTip('Stop timer')
                elapsed_seconds = int((now - active.startTime).total_seconds())
                h_s = elapsed_seconds // 3600
                m_s = (elapsed_seconds % 3600) // 60
                s_s = elapsed_seconds % 60
                elapsed_label.setText(f"{h_s:02d}:{m_s:02d}:{s_s:02d}")
                elapsed_label.setStyleSheet('color:#2ecc71;font-weight:bold;font-size:12px;')
            else:
                btn.setText('Start')
                btn.setObjectName('startBtn')
                start_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
                btn.setIcon(start_icon)
                btn.setToolTip('Start timer')
                elapsed_label.setText('00:00:00')

            # make button callback with entity id
            btn.clicked.connect(lambda _, eid=e.id: self.toggle_timer(eid))
            h.addWidget(label)
            h.addStretch()
            h.addWidget(elapsed_label)
            h.addWidget(btn)
            h.setContentsMargins(5, 2, 5, 2)
            widget.setLayout(h)
            item.setSizeHint(widget.sizeHint())
            self.timer_list.addItem(item)
            self.timer_list.setItemWidget(item, widget)
        
        # update system tray menu as well
        self.update_tray_menu()

    def toggle_timer(self, entity_id):
        entity = next((x for x in self.entities if x.id == entity_id), None)
        if not entity:
            QMessageBox.warning(self, "Error", "Entity not found")
            return
        # refresh started sessions
        started = get_started_sessions()
        active = next((s for s in started if s.entityId == entity_id), None)
        if active:
            ended = stop_session(active)
            if ended:
                QMessageBox.information(self, "Ended", f"Session {ended.id} ended for {entity.name} at {ended.endTime}")
            else:
                QMessageBox.warning(self, "Error", "Failed to end session")
        else:
            # ensure there isn't a started session for this entity
            if any(s.entityId == entity_id for s in started):
                QMessageBox.warning(self, "Error", "Entity already has a running session")
                return
            session = start_entity_session(entity)
            QMessageBox.information(self, "Started", f"Session {session.id} started for {entity.name}")
        self.refresh_all()

    def on_open_trash(self):
        dlg = TrashBinDialog(self.entities, self)
        dlg.exec()

    def load_sessions(self):
        """Load and display completed sessions filtered by entity."""
        try:
            completed = get_completed_sessions(include_deleted=False)
        except Exception:
            completed = []

        # sort by startTime descending
        sessions = sorted(completed, key=lambda s: s.startTime, reverse=True)

        # filter
        ent_id = None
        if hasattr(self, 'sessions_entity_combo'):
            ent_id = self.sessions_entity_combo.currentData()

        self.sessions_list.clear()
        for s in sessions:
            if ent_id is not None and s.entityId != ent_id:
                continue
            ent = next((e for e in self.entities if e.id == s.entityId), None)
            name = ent.name if ent else f"Entity {s.entityId}"
            start_str = s.startTime.strftime('%Y-%m-%d %H:%M:%S')
            end_str = s.endTime.strftime('%Y-%m-%d %H:%M:%S') if s.endTime else 'N/A'
            dur = int((s.endTime - s.startTime).total_seconds()) if s.endTime else 0
            h = dur // 3600
            m = (dur % 3600) // 60
            sec = dur % 60
            dur_str = f"{h}h {m}m {sec}s"

            text = f"[{s.id}] {name} — Start: {start_str} — End: {end_str} — {dur_str}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, s)
            self.sessions_list.addItem(item)

    def on_delete_session(self):
        curr = self.sessions_list.currentItem()
        if not curr:
            QMessageBox.warning(self, "Select Session", "Please select a session to delete.")
            return
        s = curr.data(Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete session {s.id}?")
        if confirm == QMessageBox.StandardButton.Yes:
            delete_session(s.id)
            self.load_sessions()

    def show_session_details(self, item):
        s = item.data(Qt.ItemDataRole.UserRole)
        ent = next((e for e in self.entities if e.id == s.entityId), None)
        name = ent.name if ent else f"Entity {s.entityId}"
        msg = f"ID: {s.id}\nEntity: {name}\nStart: {s.startTime}\nEnd: {s.endTime or 'N/A'}"
        QMessageBox.information(self, 'Session Details', msg)

    def load_reports(self):
        # Read dates from widgets if available
        try:
            start_qdate = self.start_date_edit.date()
            end_qdate = self.end_date_edit.date()
            start = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
        except Exception:
            start = datetime.now() - timedelta(days=7)
            end = datetime.now()

        if start > end:
            QMessageBox.warning(self, 'Invalid Range', 'Start date must be before or equal to end date')
            return

        if not self.entities:
            self.report_out.setHtml('<i>No entities found</i>')
            return

        ent_id = self.entity_filter_combo.currentData()
        cards = []
        for e in self.entities:
            if ent_id is not None and e.id != ent_id:
                continue
            report = generate_report(e, start, end)
            h, m, s = report.totalTimeSpent
            card = f"""
            <div style='background:#fff;padding:8px;border-radius:6px;margin:6px 0;border:1px solid #e0e0e0;'>
              <div style='font-weight:bold;color:#333;'>{e.name}</div>
              <div style='color:#555;font-size:12px;'>{h}h {m}m {s}s</div>
              <div style='color:#777;font-size:11px;'>From {start.date()} to {end.date()}</div>
            </div>
            """
            cards.append(card)

        html = "<div style='background:#f6f8fa;padding:8px;'>" + "".join(cards) + "</div>"
        self.report_out.setHtml(html)
        return

    def open_full_report(self):
        """Open the Full Report dialog with current filters pre-filled."""
        start = self.start_date_edit.date()
        end = self.end_date_edit.date()
        # aggregation not available in main Reports view; default to Day
        aggregation = 'Day'
        ent_id = self.entity_filter_combo.currentData()
        dlg = FullReportWindow(self, entities=self.entities, start_date=start, end_date=end, aggregation=aggregation, entity_filter=ent_id)
        dlg.exec()
        # refresh when done
        self.refresh_all()

    def _build_goals_tab(self):
        layout = QVBoxLayout()
        top = QHBoxLayout()
        self.goals_entity_combo = QComboBox()
        self.goals_entity_combo.addItem('-- Select Entity --', userData=None)
        self.goals_entity_combo.currentIndexChanged.connect(self.load_goals)
        
        self.add_goal_btn = QPushButton("Add Goal")
        self.add_goal_btn.clicked.connect(self.add_goal_ui)
        self.edit_goal_btn = QPushButton("Edit")
        self.edit_goal_btn.clicked.connect(self.edit_goal_ui)
        self.delete_goal_btn = QPushButton("Delete")
        self.delete_goal_btn.clicked.connect(self.delete_goal_ui)
        
        top.addWidget(QLabel("Entity:"))
        top.addWidget(self.goals_entity_combo)
        top.addStretch()
        top.addWidget(self.add_goal_btn)
        top.addWidget(self.edit_goal_btn)
        top.addWidget(self.delete_goal_btn)
        layout.addLayout(top)
        
        self.goals_list = QListWidget()
        layout.addWidget(self.goals_list)
        
        note = QLabel("Progress is calculated based on total time spent for the entity.")
        note.setStyleSheet("color:#666; font-size:11px;")
        layout.addWidget(note)
        
        self.goals_tab.setLayout(layout)

    def load_goals(self):
        ent_id = self.goals_entity_combo.currentData()
        self.goals_list.clear()
        if ent_id is None:
            return
        
        goals = get_goals(ent_id)
        # We need total time spent for this entity to show progress
        sessions = get_completed_sessions()
        ent_sessions = [s for s in sessions if s.entityId == ent_id]
        h, m, s_total = calculateTotalTime(ent_sessions)
        spent_hours = h + m/60.0 + s_total/3600.0
        
        for g in goals:
            item = QListWidgetItem()
            widget = QWidget()
            h_layout = QHBoxLayout()
            
            status_color = "#2ecc71" if g.status == "Completed" else "#f1c40f"
            name_lbl = QLabel(f"<b>{g.name}</b>")
            target_lbl = QLabel(f"{g.targetHours}h target")
            status_lbl = QLabel(g.status)
            status_lbl.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            
            progress = (spent_hours / g.targetHours * 100) if g.targetHours > 0 else 100
            progress = min(progress, 100)
            prog_lbl = QLabel(f"Progress: {progress:.1f}% ({spent_hours:.1f}h spent)")
            
            h_layout.addWidget(name_lbl)
            h_layout.addWidget(target_lbl)
            h_layout.addWidget(status_lbl)
            h_layout.addStretch()
            h_layout.addWidget(prog_lbl)
            
            widget.setLayout(h_layout)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, g)
            self.goals_list.addItem(item)
            self.goals_list.setItemWidget(item, widget)

    def add_goal_ui(self):
        ent_id = self.goals_entity_combo.currentData()
        if ent_id is None:
            QMessageBox.warning(self, "Selection", "Please select an entity first")
            return
        dlg = GoalDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, target, _ = dlg.get_data()
            if not name or target <= 0:
                QMessageBox.warning(self, "Validation", "Valid name and target hours (>0) required")
                return
            add_goal(ent_id, name, target)
            self.load_goals()

    def edit_goal_ui(self):
        item = self.goals_list.currentItem()
        if not item:
            return
        g = item.data(Qt.ItemDataRole.UserRole)
        dlg = GoalDialog(self, goal=g)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, target, status = dlg.get_data()
            update_goal(g.id, name, target, status)
            self.load_goals()

    def delete_goal_ui(self):
        item = self.goals_list.currentItem()
        if not item:
            return
        g = item.data(Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(self, "Confirm", f"Delete goal '{g.name}'?")
        if confirm == QMessageBox.StandardButton.Yes:
            delete_goal(g.id)
            self.load_goals()

class FullReportWindow(QDialog):
    def __init__(self, parent=None, entities=None, start_date=None, end_date=None, aggregation='Day', entity_filter=None):
        super().__init__(parent)
        self.setWindowTitle('Full Report')
        self.resize(900, 600)
        self.entities = entities if entities is not None else get_entities()

        layout = QVBoxLayout()
        controls = QHBoxLayout()

        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        if start_date:
            self.start_date_edit.setDate(start_date)
        else:
            self.start_date_edit.setDate(QDate.currentDate().addDays(-7))

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        if end_date:
            self.end_date_edit.setDate(end_date)
        else:
            self.end_date_edit.setDate(QDate.currentDate())

        self.aggregation_combo = QComboBox(self)
        self.aggregation_combo.addItems(['Day', 'Week', 'Month'])
        self.aggregation_combo.setCurrentText(aggregation)

        # Plot mode: Cumulative or Per-period
        self.plot_mode_combo = QComboBox(self)
        self.plot_mode_combo.addItems(['Cumulative', 'Per-period'])
        self.plot_mode_combo.setCurrentText('Cumulative')

        self.entity_filter_combo = QComboBox(self)
        self.entity_filter_combo.addItem('-- All Entities --', userData=None)
        for e in self.entities:
            self.entity_filter_combo.addItem(f"{e.id} - {e.name}", userData=e.id)
        if entity_filter is not None:
            # select specific entity
            idx = next((i for i in range(self.entity_filter_combo.count()) if self.entity_filter_combo.itemData(i) == entity_filter), 0)
            self.entity_filter_combo.setCurrentIndex(idx)

        self.generate_btn = QPushButton('Generate')
        self.generate_btn.clicked.connect(self.generate)
        self.export_csv_btn = QPushButton('Export CSV')
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_png_btn = QPushButton('Export PNG')
        self.export_png_btn.clicked.connect(self.export_png)
        self.close_btn = QPushButton('Close')
        self.close_btn.clicked.connect(self.accept) 

        # small calendar icons for date edits
        # Calendar emoji labels in Full Report dialog
        start_icon_lbl = QLabel('📅')
        start_icon_lbl.setToolTip('Start Date')
        start_icon_lbl.setStyleSheet('font-size:14px;')
        start_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_icon_lbl.setFixedWidth(22)
        self.start_date_edit.setToolTip('Start Date')
        end_icon_lbl = QLabel('📅')
        end_icon_lbl.setToolTip('End Date')
        end_icon_lbl.setStyleSheet('font-size:14px;')
        end_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        end_icon_lbl.setFixedWidth(22)
        self.end_date_edit.setToolTip('End Date')

        controls.addWidget(start_icon_lbl)
        controls.addWidget(self.start_date_edit)
        controls.addWidget(end_icon_lbl)
        controls.addWidget(self.end_date_edit)
        controls.addWidget(self.aggregation_combo)
        controls.addWidget(self.plot_mode_combo)
        controls.addWidget(self.entity_filter_combo)
        controls.addWidget(self.generate_btn)
        controls.addWidget(self.export_csv_btn)
        controls.addWidget(self.export_png_btn)
        controls.addWidget(self.close_btn)

        self.report_out = QTextEdit()
        self.report_out.setReadOnly(True)
        # Keep the report summary compact so the canvas can take most space
        self.report_out.setMaximumHeight(160)

        layout.addLayout(controls)
        layout.addWidget(self.report_out)

        # Plot area: prefer pyqtgraph for interactivity, fallback to matplotlib
        if PYQTGRAPH_AVAILABLE:
            self.plot_widget = pg.PlotWidget()
            self.plot_widget.setMinimumHeight(240)
            self.plot_widget.setBackground('w')
            layout.addWidget(self.plot_widget)
            layout.setStretch(1, 0)
            layout.setStretch(2, 1)
        elif MATPLOTLIB_AVAILABLE:
            self.canvas = FigureCanvas(Figure(figsize=(6, 3)))
            self.ax = self.canvas.figure.subplots()
            # Allow the canvas to expand to fill available space
            self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.canvas.setMinimumHeight(240)
            layout.addWidget(self.canvas)
            # Give canvas the larger stretch so it expands when resizing
            layout.setStretch(1, 0)  # index 1 = report_out
            layout.setStretch(2, 1)  # index 2 = canvas
            # ensure the matplotlib figure respects the canvas size
            self.canvas.figure.set_constrained_layout(True)
        else:
            note = QLabel('Install matplotlib or pyqtgraph to view graphs')
            note.setStyleSheet('color:#888;font-size:11px;')
            layout.addWidget(note) 

        # storage for last generated plot data (periods, labels, per_entity_agg)
        self._current_periods = []
        self._current_labels = []
        self._current_per_entity_agg = {}

        self.setLayout(layout)

    def export_csv(self):
        if not self._current_periods or not self._current_per_entity_agg:
            QMessageBox.warning(self, 'No data', 'Generate a report before exporting')
            return
        fname, _ = QFileDialog.getSaveFileName(self, 'Save CSV', filter='CSV Files (*.csv)')
        if not fname:
            return
        try:
            import csv as _csv
            # header: Period, EntityName1, EntityName2...
            entities = [e for e in self.entities if e.id in self._current_per_entity_agg]
            mode = self.plot_mode_combo.currentText().lower() if hasattr(self, 'plot_mode_combo') else 'cumulative'
            with open(fname, 'w', newline='', encoding='utf-8') as f:
                writer = _csv.writer(f)
                header = ['Period'] + [e.name for e in entities]
                writer.writerow(header)
                for idx, p in enumerate(self._current_periods):
                    row = [str(p)]
                    for e in entities:
                        ent_map = self._current_per_entity_agg.get(e.id, {})
                        seconds = ent_map.get(p, 0)
                        per_hours = seconds/3600.0
                        if mode == 'cumulative':
                            # cumulative up to this period
                            prev = sum(ent_map.get(pp, 0) for pp in self._current_periods[:idx+1]) / 3600.0
                            row.append(f"{prev:.3f}")
                        else:
                            row.append(f"{per_hours:.3f}")
                    writer.writerow(row)
            QMessageBox.information(self, 'Saved', f'CSV saved to {fname}')
        except Exception as ex:
            QMessageBox.warning(self, 'Error', f'Failed to save CSV: {ex}')

    def export_png(self):
        if not self._current_periods or not self._current_per_entity_agg:
            QMessageBox.warning(self, 'No data', 'Generate a report before exporting')
            return
        fname, _ = QFileDialog.getSaveFileName(self, 'Save PNG', filter='PNG Files (*.png)')
        if not fname:
            return
        try:
            if PYQTGRAPH_AVAILABLE:
                # grab the plot widget as pixmap
                pix = self.plot_widget.grab()
                pix.save(fname)
            elif MATPLOTLIB_AVAILABLE:
                self.canvas.figure.savefig(fname)
            else:
                raise RuntimeError('No plotting backend available')
            QMessageBox.information(self, 'Saved', f'Image saved to {fname}')
        except Exception as ex:
            QMessageBox.warning(self, 'Error', f'Failed to save PNG: {ex}')

    def generate(self):
        # Similar aggregation & plotting logic used previously, but for multiple entities
        try:
            start_qdate = self.start_date_edit.date()
            end_qdate = self.end_date_edit.date()
            start = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
        except Exception:
            start = datetime.now() - timedelta(days=7)
            end = datetime.now()

        if start > end:
            QMessageBox.warning(self, 'Invalid Range', 'Start date must be before or equal to end date')
            return

        ent_id = self.entity_filter_combo.currentData()
        agg = self.aggregation_combo.currentText().lower()

        # Build summary cards
        cards = []
        try:
            sessions = get_completed_sessions()
        except Exception:
            sessions = []

        per_entity_agg = {}
        for e in self.entities:
            if ent_id is not None and e.id != ent_id:
                continue
            report = generate_report(e, start, end)
            h, m, s = report.totalTimeSpent
            card = f"""
            <div style='background:#fff;padding:8px;border-radius:6px;margin:6px 0;border:1px solid #e0e0e0;'>
              <div style='font-weight:bold;color:#333;'>{e.name}</div>
              <div style='color:#555;font-size:12px;'>{h}h {m}m {s}s</div>
              <div style='color:#777;font-size:11px;'>From {start.date()} to {end.date()}</div>
            </div>
            """
            cards.append(card)
            # accumulate per-bucket
            ent_map = {}
            for s_obj in sessions:
                if s_obj.endTime is None:
                    continue
                if s_obj.entityId != e.id:
                    continue
                if not (s_obj.startTime >= start and s_obj.endTime <= end):
                    continue
                d = s_obj.startTime.date()
                if agg == 'day':
                    key = d
                elif agg == 'week':
                    key = d - timedelta(days=d.weekday())
                else:
                    key = d.replace(day=1)
                ent_map[key] = ent_map.get(key, 0) + (s_obj.endTime - s_obj.startTime).total_seconds()
            per_entity_agg[e.id] = ent_map

        html = "<div style='background:#f6f8fa;padding:8px;'>" + "".join(cards) + "</div>"
        self.report_out.setHtml(html)

        # Build periods and labels (common for both backends)
        # Refine start/end dates for the graph:
        # 1. Start from the earliest session date found
        # 2. End at current date (today)
        
        # Find earliest session date from all included entities in this range
        earliest_session_date = None
        for e_id, ent_map in per_entity_agg.items():
            if ent_map:
                min_d = min(ent_map.keys())
                if earliest_session_date is None or min_d < earliest_session_date:
                    earliest_session_date = min_d
        
        # fallback to the user selected start if no sessions or if earliest is after start
        graph_start = earliest_session_date if earliest_session_date else start.date()
        # Clip graph start to the range selected by the user
        if graph_start < start.date():
             graph_start = start.date()
             
        # Clip end date to today
        today = datetime.now().date()
        graph_end = min(end.date(), today)
        
        # if range is inverted after clipping, just use start/end as fallback
        if graph_start > graph_end:
            graph_start = start.date()
            graph_end = min(end.date(), today)

        periods = []
        labels = []
        cur = graph_start
        if agg == 'day':
            while cur <= graph_end:
                periods.append(cur)
                labels.append(cur.strftime('%m-%d'))
                cur = cur + timedelta(days=1)
        elif agg == 'week':
            cur = cur - timedelta(days=cur.weekday())
            while cur <= graph_end:
                periods.append(cur)
                labels.append(cur.strftime('%Y-%m-%d'))
                cur = cur + timedelta(days=7)
        else:
            cur = cur.replace(day=1)
            while cur <= graph_end:
                periods.append(cur)
                labels.append(cur.strftime('%Y-%m'))
                year = cur.year + (cur.month // 12)
                month = cur.month % 12 + 1
                cur = cur.replace(year=year, month=month, day=1)

        # store current plot data for export
        self._current_periods = periods
        self._current_labels = labels
        self._current_per_entity_agg = per_entity_agg

        # Compute series for plotting (values per period and cumulative hours)
        series_data = {}
        max_value = 0.0
        for e in self.entities:
            if ent_id is not None and e.id != ent_id:
                continue
            ent_map = per_entity_agg.get(e.id, {})
            values = [ent_map.get(p, 0) for p in periods]  # seconds per period
            per_hours = [v / 3600.0 for v in values]
            cum = []
            total = 0.0
            for h in per_hours:
                total += h
                cum.append(total)
            series_data[e.id] = {
                'name': e.name,
                'values_seconds': values,
                'per_hours': per_hours,
                'cum': cum
            }
            if per_hours:
                max_value = max(max_value, max(per_hours))
            if cum:
                max_value = max(max_value, max(cum))

        # Debug: print series summary to console to help trace issues
        print('Plot periods:', labels)
        for sid, data in series_data.items():
            print(f"Entity {sid} ({data['name']}): per_hours={data['per_hours']}, cum={data['cum']}")

        # Plot using pyqtgraph if available, otherwise matplotlib
        if PYQTGRAPH_AVAILABLE:
            try:
                self.plot_widget.clear()
                # prepare ticks
                ticks = [(i, lbl) for i, lbl in enumerate(labels)]
                ax = self.plot_widget.getAxis('bottom')
                ax.setTicks([ticks])
                # add legend (safe)
                try:
                    self.plot_widget.addLegend()
                except Exception:
                    pass
                plotted = False
                mode = self.plot_mode_combo.currentText().lower()
                for e_id, data in series_data.items():
                    y = data['cum'] if mode == 'cumulative' else data['per_hours']
                    if not any(y):
                        continue
                    pen = pg.mkPen(width=2)
                    self.plot_widget.plot(list(range(len(y))), y, pen=pen, name=data['name'], symbol='o')
                    plotted = True
                if not plotted:
                    self.plot_widget.plot([0], [0])
                else:
                    # adjust y-range with a small margin
                    top = max_value if max_value > 0 else 1.0
                    self.plot_widget.setYRange(0, top * 1.1)
            except Exception as ex:
                # surface the error to the user and console for easier debugging
                print('pyqtgraph plotting error:', ex)
                QMessageBox.warning(self, 'Plot Error', f'Failed to render pyqtgraph plot: {ex}')
        elif MATPLOTLIB_AVAILABLE:
            try:
                self.ax.clear()
                plotted = False
                mode = self.plot_mode_combo.currentText().lower()
                for e_id, data in series_data.items():
                    y = data['cum'] if mode == 'cumulative' else data['per_hours']
                    if not any(y):
                        continue
                    self.ax.plot(labels, y, marker='o', label=data['name'])
                    plotted = True

                if not plotted:
                    self.ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                else:
                    ylabel = 'Cumulative Hours' if self.plot_mode_combo.currentText() == 'Cumulative' else 'Hours per Period'
                    self.ax.set_ylabel(ylabel)
                    self.ax.set_title(f'Full Report - {self.plot_mode_combo.currentText()} ({agg})')
                    self.ax.legend(fontsize='small', loc='upper left')
                    for tick in self.ax.get_xticklabels():
                        tick.set_rotation(30)
                        tick.set_ha('right')
                    # autoscale y with margin
                    try:
                        self.ax.relim()
                        self.ax.autoscale_view()
                        ymin, ymax = self.ax.get_ylim()
                        if ymax <= ymin + 1e-6:
                            ymax = ymin + 1.0
                        self.ax.set_ylim(0, ymax * 1.1)
                    except Exception:
                        pass
                self.canvas.draw_idle()
            except Exception as ex:
                print('matplotlib plotting error:', ex)
                QMessageBox.warning(self, 'Plot Error', f'Failed to render matplotlib plot: {ex}')
        else:
            QMessageBox.information(self, 'Matplotlib missing', 'Install matplotlib or pyqtgraph to view graphs in the Full Report')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Compact, clean stylesheet for small UI
    app.setStyleSheet("""
        QMainWindow { background-color: #f0f4f8; }
        QWidget { font-family: 'Segoe UI', Arial; font-size: 11px; }
        QPushButton#startBtn { background-color: #2ecc71; color: white; border-radius: 6px; padding: 4px; }
        QPushButton#stopBtn { background-color: #e74c3c; color: white; border-radius: 6px; padding: 4px; }
        QListWidget { background: #ffffff; border: none; padding: 4px; }
        QTextEdit { background: #ffffff; border: none; padding: 6px; }
        QLabel { color: #333; }
    """)
    # Check for auto-login file
    authenticated = False
    if os.path.exists("login.txt"):
        try:
            with open("login.txt", "r") as f:
                line = f.readline().strip()
                if ',' in line:
                    u, p = line.split(',', 1)
                    from skilltrack.controller import login_user
                    if login_user(u, p):
                        authenticated = True
        except Exception:
            pass

    if not authenticated:
        # Prompt for login at startup
        login = LoginDialog()
        if login.exec() != QDialog.DialogCode.Accepted:
            # user cancelled
            sys.exit(0)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
        
    