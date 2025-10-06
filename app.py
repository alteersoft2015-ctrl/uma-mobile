import os
import sqlite3
import json
import base64
import hashlib
import paramiko
import threading
import time
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, LEFT, RIGHT

# Database class for handling SQLite operations
class UMA_DB:
    def __init__(self, db_path="uma_database.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create main_POS table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS main_POS (
            m_no INTEGER PRIMARY KEY AUTOINCREMENT,
            m_name TEXT,
            mvalue1 TEXT,
            mvalue2 TEXT,
            mvalue3 TEXT,
            mvalue4 TEXT,
            mvalue5 TEXT,
            mvalue6 TEXT,
            mvalue7 TEXT,
            mvalue8 TEXT
        )
        """)

        # Create help_POS table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS help_POS (
            h_no INTEGER PRIMARY KEY AUTOINCREMENT,
            h_name TEXT,
            hvalue1 TEXT,
            hvalue2 TEXT,
            hvalue3 TEXT,
            hvalue4 TEXT,
            hvalue5 TEXT,
            hvalue6 TEXT,
            hvalue7 TEXT,
            hvalue8 TEXT
        )
        """)

        # Create print_POS table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS print_POS (
            p_no INTEGER PRIMARY KEY AUTOINCREMENT,
            p_accounte TEXT,
            p_days TEXT,
            p_houer TEXT,
            p_price TEXT,
            p_defuser TEXT,
            p_profile TEXT,
            p_printin TEXT
        )
        """)

        # Create ready_code_POS table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ready_code_POS (
            r_no INTEGER PRIMARY KEY AUTOINCREMENT,
            r_code TEXT,
            r_comdate TEXT,
            r_getdate TEXT,
            r_status TEXT,
            r_buttom TEXT
        )
        """)

        conn.commit()
        conn.close()

    def get_help_value(self, h_no, h_value):
        """Get help value from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        column_map = {
            1: "hvalue1",
            2: "hvalue2",
            3: "hvalue3",
            4: "hvalue4",
            5: "hvalue5",
            6: "hvalue6",
            7: "hvalue7",
            8: "hvalue8"
        }

        column = column_map.get(h_value, "hvalue1")

        cursor.execute(f"SELECT {column} FROM help_POS WHERE h_no = ?", (h_no,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return result[0]
        return ""

    def get_help_value_main(self, m_no, m_value):
        """Get main value from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        column_map = {
            1: "mvalue1",
            2: "mvalue2",
            3: "mvalue3",
            4: "mvalue4",
            5: "mvalue5",
            6: "mvalue6",
            7: "mvalue7",
            8: "mvalue8"
        }

        column = column_map.get(m_value, "mvalue1")

        cursor.execute(f"SELECT {column} FROM main_POS WHERE m_no = ?", (m_no,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return result[0]
        return ""

    def save_main_settings(self, ip, username, password, connection_type, port=22):
        """Save main settings to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if record exists
        cursor.execute("SELECT * FROM main_POS WHERE m_no = 1")
        exists = cursor.fetchone()

        if exists:
            # Update existing record
            cursor.execute("""
            UPDATE main_POS SET
                mvalue1 = ?, mvalue2 = ?, mvalue3 = ?, mvalue4 = ?, mvalue5 = ?
            WHERE m_no = 1
            """, (ip, username, password, connection_type, str(port)))
        else:
            # Insert new record
            cursor.execute("""
            INSERT INTO main_POS (m_name, mvalue1, mvalue2, mvalue3, mvalue4, mvalue5)
            VALUES (?, ?, ?, ?, ?, ?)
            """, ("settings", ip, username, password, connection_type, str(port)))

        conn.commit()
        conn.close()

    def get_main_settings(self):
        """Get main settings from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT mvalue1, mvalue2, mvalue3, mvalue4, mvalue5 FROM main_POS WHERE m_no = 1")
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                "ip": result[0],
                "username": result[1],
                "password": result[2],
                "connection_type": result[3],
                "port": int(result[4]) if result[4] else 22
            }
        return {
            "ip": "",
            "username": "",
            "password": "",
            "connection_type": "ssh",
            "port": 22
        }

# MikroTik SSH handler
class MikroTikSSH:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = 30
        self.ssh = None

    def connect(self):
        """Connect to MikroTik device via SSH"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, port=self.port, username=self.username, password=self.password, timeout=self.timeout)
            return True
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from MikroTik device"""
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def execute_command(self, command):
        """Execute command on MikroTik device"""
        print(f"Executing command: {command}")
        if not self.ssh:
            print("No SSH connection, attempting to connect...")
            if not self.connect():
                print("Failed to connect via SSH")
                return None
            print("SSH connection established")

        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            # Set a timeout for reading output
            stdout.channel.settimeout(10)  # 10 seconds timeout
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            print(f"Command output: {output[:200]}...")  # Print first 200 chars
            if error:
                print(f"Command error: {error}")
                return None

            return output
        except Exception as e:
            print(f"Command execution error: {str(e)}")
            # Check if it's a timeout error
            if "timed out" in str(e).lower():
                print("Command execution timed out")
                # Try to close the connection and reconnect
                try:
                    self.disconnect()
                    self.connect()
                except:
                    pass
            return None

    def get_hotspot_users(self):
        """Get hotspot users from MikroTik device"""
        output = self.execute_command("/ip hotspot user print")
        if not output:
            return []

        print(f"Raw output: {output[:500]}...")  # Print first 500 chars for debugging

        users = []
        lines = output.strip().split('\n')
        # Find the header line to determine column positions
        header_line = None
        for line in lines:
            if "NAME" in line and "PROFILE" in line:
                header_line = line
                break

        if not header_line:
            print("Could not find header line in output")
            return users

        # Extract column positions
        name_pos = header_line.find("NAME")
        address_pos = header_line.find("ADDRESS")
        profile_pos = header_line.find("PROFILE")
        uptime_pos = header_line.find("UPTIME")

        print(f"Column positions: name={name_pos}, address={address_pos}, profile={profile_pos}, uptime={uptime_pos}")

        # Process data lines
        for line in lines:
            print(f"Processing line: {line}")
            # Skip header, separator, and comment lines
            if line.startswith("Flags") or line.startswith("---") or line.startswith("#") or not line.strip() or "NAME" in line and "PROFILE" in line:
                print(f"Skipping header/comment line")
                continue

            # Check if this is a data line (has enough length)
            if len(line) > name_pos:
                try:
                    # Extract name
                    name = ""
                    if address_pos > name_pos:
                        name = line[name_pos:address_pos].strip()

                    # Extract profile
                    profile = ""
                    if uptime_pos > profile_pos and len(line) > profile_pos:
                        profile = line[profile_pos:uptime_pos].strip()

                    # Extract uptime
                    uptime = ""
                    if len(line) > uptime_pos:
                        uptime = line[uptime_pos:].strip()

                    if name:  # Only add if we have a name
                        user = {
                            "name": name,
                            "password": "",  # Password is not shown in print output
                            "profile": profile,
                            "uptime": uptime
                        }
                        print(f"Adding user to list: {user}")
                        users.append(user)
                    else:
                        print(f"Skipping user with no name")
                except Exception as e:
                    print(f"Error processing line: {line}. Error: {str(e)}")

        print(f"Returning {len(users)} users")
        return users

    def get_hotspot_users_filtered(self, search_term):
        """Get filtered hotspot users from MikroTik device"""
        # Use server-side filtering with where clause
        output = self.execute_command(f'/ip hotspot user print where name="{search_term}"')
        if not output:
            return []

        print(f"Raw filtered output: {output[:500]}...")  # Print first 500 chars for debugging

        users = []
        lines = output.strip().split('\n')

        # Find the header line to determine column positions
        header_line = None
        for line in lines:
            if "NAME" in line and "PROFILE" in line:
                header_line = line
                break

        if not header_line:
            print("Could not find header line in output")
            return users

        # Extract column positions
        name_pos = header_line.find("NAME")
        address_pos = header_line.find("ADDRESS")
        profile_pos = header_line.find("PROFILE")
        uptime_pos = header_line.find("UPTIME")

        print(f"Column positions: name={name_pos}, address={address_pos}, profile={profile_pos}, uptime={uptime_pos}")

        # Process data lines
        for line in lines:
            print(f"Processing line: {line}")
            # Skip header, separator, and comment lines
            if line.startswith("Flags") or line.startswith("---") or line.startswith("#") or not line.strip() or "NAME" in line and "PROFILE" in line:
                print(f"Skipping header/comment line")
                continue

            # Check if this is a data line (has enough length)
            if len(line) > name_pos:
                try:
                    # Extract name
                    name = ""
                    if address_pos > name_pos:
                        name = line[name_pos:address_pos].strip()

                    # Extract profile
                    profile = ""
                    if uptime_pos > profile_pos and len(line) > profile_pos:
                        profile = line[profile_pos:uptime_pos].strip()

                    # Extract uptime
                    uptime = ""
                    if len(line) > uptime_pos:
                        uptime = line[uptime_pos:].strip()

                    if name:  # Only add if we have a name
                        user = {
                            "name": name,
                            "password": "",  # Password is not shown in print output
                            "profile": profile,
                            "uptime": uptime
                        }
                        print(f"Adding user to list: {user}")
                        users.append(user)
                    else:
                        print(f"Skipping user with no name")
                except Exception as e:
                    print(f"Error processing line: {line}. Error: {str(e)}")
            else:
                print(f"Line too short: {line}")

        print(f"Returning {len(users)} users")
        return users

    def get_user_manager_users(self):
        """Get user manager users from MikroTik device with complete details"""
        output = self.execute_command("/tool user-manager user print")
        if not output:
            return []

        users = []
        lines = output.strip().split('\n')

        # Process output lines in table format
        print("Processing output in table format")

        # Skip header lines
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            print(f"Processing line: {line}")

            # Skip header and separator lines
            if line.startswith("Flags") or line.startswith("---") or line.startswith("#") or not line.strip():
                print(f"Skipping header/comment line")
                i += 1
                continue

            # Parse the line to extract user information
            user = {
                "name": "",
                "password": "",
                "group": "",
                "uptime": "",
                "upload": "",
                "download": "",
                "transfer": "",
                "profile": "",
                "last_seen": "",
                "disabled": "false"
            }

            # Check if this line contains user information
            if "username=" in line:
                # Extract username
                parts = line.split()
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        if key == "username":
                            user["name"] = value.strip('"')
                        elif key == "customer":
                            user["group"] = value.strip('"')
                        elif key == "password":
                            user["password"] = value.strip('"')
                        elif key == "uptime-used":
                            user["uptime"] = value.strip('"')
                        elif key == "upload-used":
                            user["upload"] = value.strip('"')
                        elif key == "download-used":
                            user["download"] = value.strip('"')
                        elif key == "actual-profile":
                            user["profile"] = value.strip('"')
                        elif key == "last-seen":
                            user["last_seen"] = value.strip('"')

                # Calculate transfer total
                if user["upload"] and user["download"]:
                    try:
                        upload_mb = int(user["upload"]) / (1024 * 1024)
                        download_mb = int(user["download"]) / (1024 * 1024)
                        user["transfer"] = f"{upload_mb + download_mb:.2f} ميجا"
                    except:
                        user["transfer"] = ""

                # Only add if we have at least a name
                if user["name"]:
                    print(f"Adding user to list: {user}")
                    users.append(user)
                else:
                    print(f"Skipping user with no name: {user}")

            i += 1

        print(f"Returning {len(users)} users")
        return users

    def get_user_manager_users_filtered(self, search_term):
        """Get filtered user manager users from MikroTik device"""
        print(f"Searching for user manager users with term: {search_term}")

        # Use server-side filtering with where clause
        script = f'/tool user-manager user print where username~"{search_term}"'
        print(f"Script to execute: {script}")

        output = self.execute_command(script)
        if not output:
            print("No output received from command")
            return []

        print(f"Raw filtered output: {output[:500]}...")  # Print first 500 chars for debugging

        users = []
        lines = output.strip().split('\n')
        print(f"Number of lines in output: {len(lines)}")

        # Process output lines in table format
        print("Processing output in table format")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            print(f"Processing line: {line}")

            # Skip header and separator lines
            if line.startswith("Flags") or line.startswith("---") or line.startswith("#") or not line.strip():
                print(f"Skipping header/comment line")
                i += 1
                continue

            # Parse the line to extract user information
            user = {
                "name": "",
                "password": "",
                "group": "",
                "uptime": "",
                "upload": "",
                "download": "",
                "transfer": "",
                "profile": "",
                "last_seen": "",
                "disabled": "false"
            }

            # Check if this line contains user information
            if "username=" in line:
                # Extract username
                parts = line.split()
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        if key == "username":
                            user["name"] = value.strip('"')
                        elif key == "customer":
                            user["group"] = value.strip('"')
                        elif key == "password":
                            user["password"] = value.strip('"')
                        elif key == "uptime-used":
                            user["uptime"] = value.strip('"')
                        elif key == "upload-used":
                            user["upload"] = value.strip('"')
                        elif key == "download-used":
                            user["download"] = value.strip('"')
                        elif key == "actual-profile":
                            user["profile"] = value.strip('"')
                        elif key == "last-seen":
                            user["last_seen"] = value.strip('"')

                # Calculate transfer total
                if user["upload"] and user["download"]:
                    try:
                        upload_mb = int(user["upload"]) / (1024 * 1024)
                        download_mb = int(user["download"]) / (1024 * 1024)
                        user["transfer"] = f"{upload_mb + download_mb:.2f} ميجا"
                    except:
                        user["transfer"] = ""

                # Only add if we have at least a name
                if user["name"]:
                    print(f"Adding user to list: {user}")
                    users.append(user)
                else:
                    print(f"Skipping user with no name: {user}")

            i += 1

        print(f"Returning {len(users)} users")
        return users

# Main application window
class UMAMobileApp(toga.App):
    def startup(self):
        self.db = UMA_DB()
        self.api = None

        # Create a main window with a name
        self.main_window = toga.MainWindow(title=self.name)

        # Create a tab group
        self.tab_group = toga.OptionContainer()

        # Create tabs
        self.connection_tab = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.search_tab = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.settings_tab = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Add tabs to tab group
        self.tab_group.add("الاتصال", self.connection_tab)
        self.tab_group.add("البحث", self.search_tab)
        self.tab_group.add("الإعدادات", self.settings_tab)

        # Initialize tabs
        self.init_connection_tab()
        self.init_search_tab()
        self.init_settings_tab()

        # Add tab group to main window
        self.main_window.content = self.tab_group

        # Show the main window
        self.main_window.show()

        # Load settings
        self.load_settings()

    def init_connection_tab(self):
        """Initialize connection tab"""
        # Connection form
        connection_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # IP Address
        ip_box = toga.Box(style=Pack(direction=ROW, padding=5))
        ip_label = toga.Label("عنوان IP:", style=Pack(text_align=RIGHT, width=100))
        self.ip_input = toga.TextInput(style=Pack(flex=1))
        ip_box.add(ip_label)
        ip_box.add(self.ip_input)
        connection_box.add(ip_box)

        # Username
        username_box = toga.Box(style=Pack(direction=ROW, padding=5))
        username_label = toga.Label("اسم المستخدم:", style=Pack(text_align=RIGHT, width=100))
        self.username_input = toga.TextInput(style=Pack(flex=1))
        username_box.add(username_label)
        username_box.add(self.username_input)
        connection_box.add(username_box)

        # Password
        password_box = toga.Box(style=Pack(direction=ROW, padding=5))
        password_label = toga.Label("كلمة المرور:", style=Pack(text_align=RIGHT, width=100))
        self.password_input = toga.PasswordInput(style=Pack(flex=1))
        password_box.add(password_label)
        password_box.add(self.password_input)
        connection_box.add(password_box)

        # Port
        port_box = toga.Box(style=Pack(direction=ROW, padding=5))
        port_label = toga.Label("المنفذ:", style=Pack(text_align=RIGHT, width=100))
        self.port_input = toga.TextInput(value="22", style=Pack(flex=1))
        port_box.add(port_label)
        port_box.add(self.port_input)
        connection_box.add(port_box)

        # Connect button
        self.connect_button = toga.Button(
            "اتصال",
            on_press=self.connect_to_device,
            style=Pack(padding=10)
        )
        connection_box.add(self.connect_button)

        # Status label
        self.status_label = toga.Label(
            "الحالة: غير متصل",
            style=Pack(text_align=CENTER, padding=10)
        )
        connection_box.add(self.status_label)

        self.connection_tab.add(connection_box)

    def init_search_tab(self):
        """Initialize search tab"""
        # Search form
        search_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Search type
        type_box = toga.Box(style=Pack(direction=ROW, padding=5))
        type_label = toga.Label("نوع البحث:", style=Pack(text_align=RIGHT, width=100))
        self.search_type = toga.Selection(items=[
            ("HotSpot", "hotspot"),
            ("User Manager", "userman")
        ], style=Pack(flex=1))
        self.search_type.value = "hotspot"
        type_box.add(type_label)
        type_box.add(self.search_type)
        search_box.add(type_box)

        # Search term
        search_term_box = toga.Box(style=Pack(direction=ROW, padding=5))
        search_term_label = toga.Label("اسم المستخدم:", style=Pack(text_align=RIGHT, width=100))
        self.search_term_input = toga.TextInput(style=Pack(flex=1))
        search_term_box.add(search_term_label)
        search_term_box.add(self.search_term_input)
        search_box.add(search_term_box)

        # Search button
        self.search_button = toga.Button(
            "بحث",
            on_press=self.search_users,
            style=Pack(padding=10)
        )
        search_box.add(self.search_button)

        # Info text
        info_text = """تعليمات الاستخدام:
- اترك حقل البحث فارغاً لعرض جميع المستخدمين
- أدخل جزء من اسم المستخدم للبحث الجزئي
- HotSpot: لعرض مستخدمي النقاط الساخنة
- User Manager: لعرض مستخدمي مدير المستخدمين"""

        info_label = toga.Label(
            info_text,
            style=Pack(text_align=RIGHT, padding=10)
        )
        search_box.add(info_label)

        self.search_tab.add(search_box)

    def init_settings_tab(self):
        """Initialize settings tab"""
        # Settings form
        settings_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Settings info
        info_text = """إعدادات التطبيق

يتم حفظ إعدادات الاتصال تلقائياً في قاعدة بيانات محلية.

الميزات المتاحة:
• الاتصال بأجهزة MikroTik عبر SSH
• البحث في مستخدمي HotSpot و User Manager
• عرض النتائج بشكل منظم
• واجهة مستخدم عربية

للإبلاغ عن مشاكل أو اقتراح تحسينات، يرجى مراجعة المطور."""

        info_label = toga.Label(
            info_text,
            style=Pack(text_align=RIGHT, padding=10)
        )
        settings_box.add(info_label)

        # Save settings button
        self.save_settings_button = toga.Button(
            "حفظ الإعدادات",
            on_press=self.save_settings,
            style=Pack(padding=10)
        )
        settings_box.add(self.save_settings_button)

        self.settings_tab.add(settings_box)

    def load_settings(self):
        """Load settings from database"""
        settings = self.db.get_main_settings()
        self.ip_input.value = settings["ip"]
        self.username_input.value = settings["username"]
        self.password_input.value = settings["password"]
        self.port_input.value = str(settings["port"])

    def save_settings(self, widget):
        """Save settings to database"""
        ip = self.ip_input.value
        username = self.username_input.value
        password = self.password_input.value
        port = self.port_input.value

        try:
            port = int(port)
        except ValueError:
            port = 22

        self.db.save_main_settings(ip, username, password, "ssh", port)
        self.main_window.info_dialog(
            "نجاح",
            "تم حفظ الإعدادات بنجاح"
        )

    def connect_to_device(self, widget):
        """Connect to MikroTik device"""
        ip = self.ip_input.value
        username = self.username_input.value
        password = self.password_input.value
        port_str = self.port_input.value

        if not ip or not username or not password:
            self.main_window.error_dialog(
                "خطأ",
                "الرجاء إدخال جميع بيانات الاتصال"
            )
            return

        try:
            port = int(port_str)
        except ValueError:
            port = 22

        self.api = MikroTikSSH(ip, username, password, port)

        # Test connection in a separate thread
        def test_connection():
            self.status_label.text = "الحالة: جاري الاتصال..."
            success = self.api.connect()

            # Update UI in main thread
            if success:
                self.status_label.text = "الحالة: متصل ✅"
                self.main_window.info_dialog(
                    "نجاح",
                    "تم الاتصال بالجهاز بنجاح"
                )
            else:
                self.status_label.text = "الحالة: فشل الاتصال ❌"
                self.main_window.error_dialog(
                    "خطأ",
                    "فشل الاتصال بالجهاز"
                )

        threading.Thread(target=test_connection, daemon=True).start()

    def search_users(self, widget):
        """Search for users"""
        if not self.api:
            self.main_window.error_dialog(
                "خطأ",
                "الرجاء الاتصال بالجهاز أولاً"
            )
            return

        search_term = self.search_term_input.value
        search_type = self.search_type.value

        # Search in a separate thread
        def search():
            if search_type == "hotspot":
                if search_term:
                    users = self.api.get_hotspot_users_filtered(search_term)
                else:
                    users = self.api.get_hotspot_users()
            else:
                if search_term:
                    users = self.api.get_user_manager_users_filtered(search_term)
                else:
                    users = self.api.get_user_manager_users()

            # Display results in main thread
            self.display_search_results(users, search_type)

        threading.Thread(target=search, daemon=True).start()

    def display_search_results(self, users, search_type):
        """Display search results"""
        if not users:
            self.main_window.info_dialog(
                "نتائج البحث",
                "لم يتم العثور على أي مستخدمين"
            )
            return

        # Create result text
        result_text = f"تم العثور على {len(users)} مستخدم:\n\n"

        for i, user in enumerate(users, 1):
            result_text += f"المستخدم {i}:\n"

            if search_type == "hotspot":
                result_text += f"   الاسم: {user.get('name', '')}\n"
                result_text += f"   الملف الشخصي: {user.get('profile', '')}\n"
                if user.get('uptime'):
                    result_text += f"   مدة التشغيل: {user.get('uptime', '')}\n"
                if user.get('bytes-out'):
                    result_text += f"   التحميل: {user.get('bytes-out', '')}\n"
                if user.get('bytes-in'):
                    result_text += f"   الرفع: {user.get('bytes-in', '')}\n"
            else:
                result_text += f"   الاسم: {user.get('name', '')}\n"
                if user.get('group'):
                    result_text += f"   المجموعة: {user.get('group', '')}\n"
                result_text += f"   الملف الشخصي: {user.get('profile', '')}\n"
                if user.get('uptime'):
                    result_text += f"   مدة التشغيل: {user.get('uptime', '')}\n"
                if user.get('download'):
                    result_text += f"   التحميل: {user.get('download', '')}\n"
                if user.get('upload'):
                    result_text += f"   الرفع: {user.get('upload', '')}\n"
                if user.get('last-seen'):
                    result_text += f"   آخر ظهور: {user.get('last-seen', '')}\n"

            result_text += "\n" + "─" * 50 + "\n\n"

        # Show results in dialog
        self.main_window.info_dialog(
            "نتائج البحث",
            result_text
        )

def main():
    return UMAMobileApp("UMA", "com.example.uma")

if __name__ == "__main__":
    main().main_loop()
