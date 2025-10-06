import os
import sqlite3
import json
import base64
import hashlib
import paramiko
import threading
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.metrics import dp

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

        print(f"Returning {len(users)} users")
        return users

    def get_user_manager_users(self):
        """Get user manager users from MikroTik device"""
        output = self.execute_command("/tool user-manager user print")
        if not output:
            return []

        print(f"Raw output: {output[:500]}...")  # Print first 500 chars for debugging

        users = []
        lines = output.strip().split('\n')
        # Find the header line to determine column positions
        header_line = None
        for line in lines:
            if "USERNAME" in line and "PASSWORD" in line:
                header_line = line
                break

        if not header_line:
            print("Could not find header line in output")
            return users

        # Extract column positions
        username_pos = header_line.find("USERNAME")
        password_pos = header_line.find("PASSWORD")
        uptime_pos = header_line.find("UPTIME")

        print(f"Column positions: username={username_pos}, password={password_pos}, uptime={uptime_pos}")

        # Process data lines
        for line in lines:
            print(f"Processing line: {line}")
            # Skip header, separator, and comment lines
            if line.startswith("Flags") or line.startswith("---") or line.startswith("#") or not line.strip() or "USERNAME" in line and "PASSWORD" in line:
                print(f"Skipping header/comment line")
                continue

            # Check if this is a data line (has enough length)
            if len(line) > username_pos:
                try:
                    # Extract username
                    username = ""
                    if password_pos > username_pos:
                        username = line[username_pos:password_pos].strip()

                    # Extract password
                    password = ""
                    if uptime_pos > password_pos and len(line) > password_pos:
                        password = line[password_pos:uptime_pos].strip()

                    # Extract uptime
                    uptime = ""
                    if len(line) > uptime_pos:
                        uptime = line[uptime_pos:].strip()

                    if username:  # Only add if we have a username
                        user = {
                            "name": username,
                            "password": password,
                            "uptime": uptime
                        }
                        print(f"Adding user to list: {user}")
                        users.append(user)
                    else:
                        print(f"Skipping user with no username")
                except Exception as e:
                    print(f"Error processing line: {line}. Error: {str(e)}")

        print(f"Returning {len(users)} users")
        return users

    def get_user_manager_users_filtered(self, search_term):
        """Get filtered user manager users from MikroTik device"""
        # Use server-side filtering with where clause
        output = self.execute_command(f'/tool user-manager user print where username="{search_term}"')
        if not output:
            return []

        print(f"Raw filtered output: {output[:500]}...")  # Print first 500 chars for debugging

        users = []
        lines = output.strip().split('\n')

        # Find the header line to determine column positions
        header_line = None
        for line in lines:
            if "USERNAME" in line and "PASSWORD" in line:
                header_line = line
                break

        if not header_line:
            print("Could not find header line in output")
            return users

        # Extract column positions
        username_pos = header_line.find("USERNAME")
        password_pos = header_line.find("PASSWORD")
        uptime_pos = header_line.find("UPTIME")

        print(f"Column positions: username={username_pos}, password={password_pos}, uptime={uptime_pos}")

        # Process data lines
        for line in lines:
            print(f"Processing line: {line}")
            # Skip header, separator, and comment lines
            if line.startswith("Flags") or line.startswith("---") or line.startswith("#") or not line.strip() or "USERNAME" in line and "PASSWORD" in line:
                print(f"Skipping header/comment line")
                continue

            # Check if this is a data line (has enough length)
            if len(line) > username_pos:
                try:
                    # Extract username
                    username = ""
                    if password_pos > username_pos:
                        username = line[username_pos:password_pos].strip()

                    # Extract password
                    password = ""
                    if uptime_pos > password_pos and len(line) > password_pos:
                        password = line[password_pos:uptime_pos].strip()

                    # Extract uptime
                    uptime = ""
                    if len(line) > uptime_pos:
                        uptime = line[uptime_pos:].strip()

                    if username:  # Only add if we have a username
                        user = {
                            "name": username,
                            "password": password,
                            "uptime": uptime
                        }
                        print(f"Adding user to list: {user}")
                        users.append(user)
                    else:
                        print(f"Skipping user with no username")
                except Exception as e:
                    print(f"Error processing line: {line}. Error: {str(e)}")

        print(f"Returning {len(users)} users")
        return users

# Main App class
class UMAApp(App):
    def build(self):
        # Set app title
        self.title = "UMA - MikroTik User Manager"

        # Initialize database
        self.db = UMA_DB()

        # Create main layout
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Create tabbed panel
        self.tab_panel = TabbedPanel(do_default_tab=False)

        # Create settings tab
        self.settings_tab = TabbedPanelItem(text='الإعدادات')
        self.create_settings_tab()
        self.tab_panel.add_widget(self.settings_tab)

        # Create hotspot tab
        self.hotspot_tab = TabbedPanelItem(text='HotSpot')
        self.create_hotspot_tab()
        self.tab_panel.add_widget(self.hotspot_tab)

        # Create user manager tab
        self.user_manager_tab = TabbedPanelItem(text='User Manager')
        self.create_user_manager_tab()
        self.tab_panel.add_widget(self.user_manager_tab)

        # Add tab panel to main layout
        self.main_layout.add_widget(self.tab_panel)

        return self.main_layout

    def create_settings_tab(self):
        # Create settings layout
        settings_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Get saved settings
        settings = self.db.get_main_settings()

        # IP address input
        ip_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        ip_label = Label(text='IP:', size_hint_x=0.3)
        self.ip_input = TextInput(text=settings['ip'], multiline=False)
        ip_layout.add_widget(ip_label)
        ip_layout.add_widget(self.ip_input)
        settings_layout.add_widget(ip_layout)

        # Username input
        username_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        username_label = Label(text='Username:', size_hint_x=0.3)
        self.username_input = TextInput(text=settings['username'], multiline=False)
        username_layout.add_widget(username_label)
        username_layout.add_widget(self.username_input)
        settings_layout.add_widget(username_layout)

        # Password input
        password_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        password_label = Label(text='Password:', size_hint_x=0.3)
        self.password_input = TextInput(text=settings['password'], multiline=False, password=True)
        password_layout.add_widget(password_label)
        password_layout.add_widget(self.password_input)
        settings_layout.add_widget(password_layout)

        # Port input
        port_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        port_label = Label(text='Port:', size_hint_x=0.3)
        self.port_input = TextInput(text=str(settings['port']), multiline=False)
        port_layout.add_widget(port_label)
        port_layout.add_widget(self.port_input)
        settings_layout.add_widget(port_layout)

        # Connection type
        connection_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        connection_label = Label(text='Connection:', size_hint_x=0.3)
        self.connection_input = TextInput(text=settings['connection_type'], multiline=False)
        connection_layout.add_widget(connection_label)
        connection_layout.add_widget(self.connection_input)
        settings_layout.add_widget(connection_layout)

        # Save button
        save_button = Button(text='حفظ الإعدادات', size_hint_y=None, height=dp(50))
        save_button.bind(on_press=self.save_settings)
        settings_layout.add_widget(save_button)

        # Add settings layout to settings tab
        self.settings_content = ScrollView()
        self.settings_content.add_widget(settings_layout)
        self.settings_tab.content = self.settings_content

    def create_hotspot_tab(self):
        # Create hotspot layout
        hotspot_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Search input
        search_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        search_label = Label(text='Search:', size_hint_x=0.3)
        self.hotspot_search_input = TextInput(multiline=False)
        search_layout.add_widget(search_label)
        search_layout.add_widget(self.hotspot_search_input)
        hotspot_layout.add_widget(search_layout)

        # Search button
        search_button = Button(text='بحث', size_hint_y=None, height=dp(50))
        search_button.bind(on_press=self.search_hotspot_users)
        hotspot_layout.add_widget(search_button)

        # Results area
        self.hotspot_results_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.hotspot_results_layout.bind(minimum_height=self.hotspot_results_layout.setter('height'))

        self.hotspot_results_scroll = ScrollView()
        self.hotspot_results_scroll.add_widget(self.hotspot_results_layout)
        hotspot_layout.add_widget(self.hotspot_results_scroll)

        # Add hotspot layout to hotspot tab
        self.hotspot_tab.content = hotspot_layout

    def create_user_manager_tab(self):
        # Create user manager layout
        user_manager_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Search input
        search_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        search_label = Label(text='Search:', size_hint_x=0.3)
        self.user_manager_search_input = TextInput(multiline=False)
        search_layout.add_widget(search_label)
        search_layout.add_widget(self.user_manager_search_input)
        user_manager_layout.add_widget(search_layout)

        # Search button
        search_button = Button(text='بحث', size_hint_y=None, height=dp(50))
        search_button.bind(on_press=self.search_user_manager_users)
        user_manager_layout.add_widget(search_button)

        # Results area
        self.user_manager_results_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.user_manager_results_layout.bind(minimum_height=self.user_manager_results_layout.setter('height'))

        self.user_manager_results_scroll = ScrollView()
        self.user_manager_results_scroll.add_widget(self.user_manager_results_layout)
        user_manager_layout.add_widget(self.user_manager_results_scroll)

        # Add user manager layout to user manager tab
        self.user_manager_tab.content = user_manager_layout

    def save_settings(self, instance):
        # Get values from inputs
        ip = self.ip_input.text
        username = self.username_input.text
        password = self.password_input.text
        try:
            port = int(self.port_input.text)
        except ValueError:
            port = 22
        connection_type = self.connection_input.text

        # Save to database
        self.db.save_main_settings(ip, username, password, connection_type, port)

        # Show success message
        popup = Popup(title='نجاح', content=Label(text='تم حفظ الإعدادات بنجاح'), size_hint=(0.8, 0.4))
        popup.open()

    def search_hotspot_users(self, instance):
        # Get search term
        search_term = self.hotspot_search_input.text

        # Clear previous results
        self.hotspot_results_layout.clear_widgets()

        # Get settings
        settings = self.db.get_main_settings()

        # Check if settings are valid
        if not settings['ip'] or not settings['username']:
            popup = Popup(title='خطأ', content=Label(text='يرجى إدخال IP و Username في الإعدادات'), size_hint=(0.8, 0.4))
            popup.open()
            return

        # Create SSH connection
        ssh = MikroTikSSH(settings['ip'], settings['username'], settings['password'], settings['port'])

        # Connect to device
        if not ssh.connect():
            popup = Popup(title='خطأ', content=Label(text='فشل الاتصال بالجهاز'), size_hint=(0.8, 0.4))
            popup.open()
            return

        # Search for users
        if search_term:
            users = ssh.get_hotspot_users_filtered(search_term)
        else:
            users = ssh.get_hotspot_users()

        # Disconnect from device
        ssh.disconnect()

        # Display results
        if not users:
            self.hotspot_results_layout.add_widget(Label(text='لم يتم العثور على مستخدمين'))
        else:
            for user in users:
                user_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(5))

                name_label = Label(text=f"Name: {user['name']}", size_hint_y=None, height=dp(30))
                profile_label = Label(text=f"Profile: {user['profile']}", size_hint_y=None, height=dp(30))
                uptime_label = Label(text=f"Uptime: {user['uptime']}", size_hint_y=None, height=dp(30))

                user_layout.add_widget(name_label)
                user_layout.add_widget(profile_label)
                user_layout.add_widget(uptime_label)

                self.hotspot_results_layout.add_widget(user_layout)

    def search_user_manager_users(self, instance):
        # Get search term
        search_term = self.user_manager_search_input.text

        # Clear previous results
        self.user_manager_results_layout.clear_widgets()

        # Get settings
        settings = self.db.get_main_settings()

        # Check if settings are valid
        if not settings['ip'] or not settings['username']:
            popup = Popup(title='خطأ', content=Label(text='يرجى إدخال IP و Username في الإعدادات'), size_hint=(0.8, 0.4))
            popup.open()
            return

        # Create SSH connection
        ssh = MikroTikSSH(settings['ip'], settings['username'], settings['password'], settings['port'])

        # Connect to device
        if not ssh.connect():
            popup = Popup(title='خطأ', content=Label(text='فشل الاتصال بالجهاز'), size_hint=(0.8, 0.4))
            popup.open()
            return

        # Search for users
        if search_term:
            users = ssh.get_user_manager_users_filtered(search_term)
        else:
            users = ssh.get_user_manager_users()

        # Disconnect from device
        ssh.disconnect()

        # Display results
        if not users:
            self.user_manager_results_layout.add_widget(Label(text='لم يتم العثور على مستخدمين'))
        else:
            for user in users:
                user_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(5))

                name_label = Label(text=f"Username: {user['name']}", size_hint_y=None, height=dp(30))
                password_label = Label(text=f"Password: {user['password']}", size_hint_y=None, height=dp(30))
                uptime_label = Label(text=f"Uptime: {user['uptime']}", size_hint_y=None, height=dp(30))

                user_layout.add_widget(name_label)
                user_layout.add_widget(password_label)
                user_layout.add_widget(uptime_label)

                self.user_manager_results_layout.add_widget(user_layout)

# Run the app
if __name__ == '__main__':
    UMAApp().run()
