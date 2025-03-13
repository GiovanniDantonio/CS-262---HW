"""
Persistence module for fault-tolerant chat system.
Handles storage of log entries, state snapshots, and system metadata.
"""
import json
import logging
import os
import sqlite3
import threading
import time
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("persistence")

class PersistentStorage:
    """
    Handles persistent storage of log entries and state.
    Supports write-ahead logging and snapshots for efficient recovery.
    """
    
    def __init__(self, server_id: str, data_dir: str):
        """
        Initialize the persistent storage.
        
        Args:
            server_id: Unique identifier for this server
            data_dir: Directory where data files will be stored
        """
        self.server_id = server_id
        self.data_dir = os.path.join(data_dir, server_id)
        self.metadata_file = os.path.join(self.data_dir, "metadata.json")
        self.log_file = os.path.join(self.data_dir, "raft-log.json")
        self.snapshot_file = os.path.join(self.data_dir, "snapshot.db")
        self.mutex = threading.RLock()
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize the database
        self._init_database()
        
    def _init_database(self) -> None:
        """
        Initialize the SQLite database for message storage.
        Creates necessary tables if they don't exist.
        """
        conn = sqlite3.connect(self.snapshot_file)
        try:
            c = conn.cursor()
            # Users table
            c.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Messages table
            c.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read INTEGER DEFAULT 0,
                    sequence_number INTEGER NOT NULL,
                    FOREIGN KEY (sender) REFERENCES accounts(username),
                    FOREIGN KEY (recipient) REFERENCES accounts(username)
                )
            ''')
            
            # Index for faster message retrieval
            c.execute('CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_messages_sequence ON messages(sequence_number)')
            conn.commit()
        finally:
            conn.close()
            
    def save_metadata(self, current_term: int, voted_for: Optional[str]) -> None:
        """
        Save Raft metadata to disk.
        
        Args:
            current_term: Current term number
            voted_for: Candidate that received vote in current term (if any)
        """
        with self.mutex:
            metadata = {
                "current_term": current_term,
                "voted_for": voted_for,
                "last_updated": time.time()
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f)
    
    def load_metadata(self) -> Tuple[int, Optional[str]]:
        """
        Load Raft metadata from disk.
        
        Returns:
            Tuple of (current_term, voted_for)
        """
        with self.mutex:
            if not os.path.exists(self.metadata_file):
                return 0, None
                
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                
            return metadata.get("current_term", 0), metadata.get("voted_for", None)
    
    def append_log_entries(self, entries: List[Dict[str, Any]]) -> None:
        """
        Append log entries to the persistent log.
        
        Args:
            entries: List of log entries to append
        """
        with self.mutex:
            # Append entries to the log file in a durable way
            with open(self.log_file, 'a') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
    
    def read_log_entries(self) -> List[Dict[str, Any]]:
        """
        Read all log entries from disk.
        
        Returns:
            List of log entries
        """
        entries = []
        with self.mutex:
            if not os.path.exists(self.log_file):
                return entries
                
            with open(self.log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        return entries
    
    def truncate_log(self, last_index: int) -> None:
        """
        Truncate the log to remove entries after last_index.
        Used when the leader instructs to discard conflicting entries.
        
        Args:
            last_index: Index after which entries should be removed
        """
        with self.mutex:
            if not os.path.exists(self.log_file):
                return
                
            # Read existing entries
            entries = self.read_log_entries()
            
            # Keep only entries up to last_index
            valid_entries = [e for e in entries if e["index"] <= last_index]
            
            # Write back the truncated log
            with open(self.log_file, 'w') as f:
                for entry in valid_entries:
                    f.write(json.dumps(entry) + '\n')
                f.flush()
                os.fsync(f.fileno())
    
    def create_snapshot(self, last_included_index: int, last_included_term: int) -> None:
        """
        Create a snapshot of the current state up to last_included_index.
        
        Args:
            last_included_index: Index of last entry included in snapshot
            last_included_term: Term of last entry included in snapshot
        """
        with self.mutex:
            # Save snapshot metadata
            metadata = {
                "last_included_index": last_included_index,
                "last_included_term": last_included_term,
                "timestamp": time.time()
            }
            
            with open(os.path.join(self.data_dir, "snapshot-meta.json"), 'w') as f:
                json.dump(metadata, f)
                
            # The SQLite database already contains the snapshot of the state machine
            # So we just need to persist it through a checkpoint
            conn = sqlite3.connect(self.snapshot_file)
            try:
                conn.execute("PRAGMA wal_checkpoint(FULL)")
            finally:
                conn.close()
                
            # Truncate the log to remove entries included in the snapshot
            new_log_file = self.log_file + ".new"
            with open(self.log_file, 'r') as old_f, open(new_log_file, 'w') as new_f:
                for line in old_f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry["index"] > last_included_index:
                            new_f.write(line)
                new_f.flush()
                os.fsync(new_f.fileno())
                
            # Replace the old log file with the new one
            os.replace(new_log_file, self.log_file)
    
    def load_snapshot(self) -> Tuple[int, int]:
        """
        Load snapshot metadata.
        
        Returns:
            Tuple of (last_included_index, last_included_term)
        """
        snapshot_meta_file = os.path.join(self.data_dir, "snapshot-meta.json")
        if not os.path.exists(snapshot_meta_file):
            return -1, 0
            
        with open(snapshot_meta_file, 'r') as f:
            metadata = json.load(f)
            
        return metadata.get("last_included_index", -1), metadata.get("last_included_term", 0)
            
    def apply_command_to_state_machine(self, command: Dict[str, Any]) -> Any:
        """
        Apply a command to the state machine (SQLite database).
        
        Args:
            command: Command to apply
            
        Returns:
            Result of the command
        """
        # Connect to the database
        conn = sqlite3.connect(self.snapshot_file)
        conn.row_factory = sqlite3.Row
        
        try:
            # Process command based on type
            command_type = command.get("type")
            
            if command_type == "register":
                return self._handle_register(conn, command)
            elif command_type == "login":
                return self._handle_login(conn, command)
            elif command_type == "send_message":
                return self._handle_send_message(conn, command)
            elif command_type == "delete_messages":
                return self._handle_delete_messages(conn, command)
            elif command_type == "mark_as_read":
                return self._handle_mark_as_read(conn, command)
            elif command_type == "delete_account":
                return self._handle_delete_account(conn, command)
            else:
                logger.warning(f"Unknown command type: {command_type}")
                return {"success": False, "message": "Unknown command type"}
        finally:
            conn.close()
            
    def _handle_register(self, conn: sqlite3.Connection, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user registration command.
        
        Args:
            conn: Database connection
            command: Registration command
            
        Returns:
            Result of registration
        """
        c = conn.cursor()
        try:
            c.execute("INSERT INTO accounts (username, password) VALUES (?, ?)",
                     (command["username"], command["password"]))
            conn.commit()
            return {"success": True, "message": "Account created successfully."}
        except sqlite3.IntegrityError:
            return {"success": False, "message": "Username already exists."}
        except Exception as e:
            logger.error(f"Error in register: {e}")
            return {"success": False, "message": "Account creation failed."}
            
    def _handle_login(self, conn: sqlite3.Connection, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user login command.
        
        Args:
            conn: Database connection
            command: Login command
            
        Returns:
            Result of login
        """
        c = conn.cursor()
        c.execute("SELECT password FROM accounts WHERE username = ?", (command["username"],))
        record = c.fetchone()
        
        if not record or record["password"] != command["password"]:
            return {"success": False, "message": "Invalid username or password.", "unread_count": 0}
            
        # Update last_login
        c.execute("UPDATE accounts SET last_login = ? WHERE username = ?",
                 (command["timestamp"] if "timestamp" in command else time.time(), command["username"]))
                 
        # Count unread messages
        c.execute("SELECT COUNT(*) AS count FROM messages WHERE recipient = ? AND read = 0", 
                 (command["username"],))
        result = c.fetchone()
        unread_count = result["count"] if result else 0
        
        conn.commit()
        return {
            "success": True, 
            "message": "Login successful.", 
            "unread_count": unread_count
        }
            
    def _handle_send_message(self, conn: sqlite3.Connection, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle send message command.
        
        Args:
            conn: Database connection
            command: Send message command
            
        Returns:
            Result of sending message
        """
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO messages (sender, recipient, content, read, sequence_number, timestamp) 
                VALUES (?, ?, ?, 0, ?, ?)
            """, (
                command["sender"], 
                command["recipient"], 
                command["content"],
                command.get("sequence_number", 0),
                command.get("timestamp", time.time())
            ))
            message_id = c.lastrowid
            conn.commit()
            return {"success": True, "message": "Message sent successfully.", "id": message_id}
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return {"success": False, "message": "Failed to send message."}
            
    def _handle_delete_messages(self, conn: sqlite3.Connection, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delete messages command.
        
        Args:
            conn: Database connection
            command: Delete messages command
            
        Returns:
            Result of deletion
        """
        if not command.get("message_ids"):
            return {"success": False, "message": "No message IDs provided."}
            
        c = conn.cursor()
        try:
            placeholders = ','.join('?' for _ in command["message_ids"])
            params = list(command["message_ids"]) + [command["username"], command["username"]]
            c.execute(f"DELETE FROM messages WHERE id IN ({placeholders}) AND (sender = ? OR recipient = ?)", params)
            deleted_count = c.rowcount
            conn.commit()
            return {"success": True, "message": f"Deleted {deleted_count} messages."}
        except Exception as e:
            logger.error(f"Error in delete_messages: {e}")
            return {"success": False, "message": "Failed to delete messages."}
            
    def _handle_mark_as_read(self, conn: sqlite3.Connection, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mark messages as read command.
        
        Args:
            conn: Database connection
            command: Mark as read command
            
        Returns:
            Result of operation
        """
        if not command.get("message_ids"):
            return {"success": False, "message": "No message IDs provided."}
            
        c = conn.cursor()
        try:
            placeholders = ','.join('?' for _ in command["message_ids"])
            params = list(command["message_ids"]) + [command["username"]]
            c.execute(f"UPDATE messages SET read = 1 WHERE id IN ({placeholders}) AND recipient = ?", params)
            marked_count = c.rowcount
            conn.commit()
            return {"success": True, "message": f"Marked {marked_count} messages as read."}
        except Exception as e:
            logger.error(f"Error in mark_as_read: {e}")
            return {"success": False, "message": "Failed to mark messages as read."}
            
    def _handle_delete_account(self, conn: sqlite3.Connection, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delete account command.
        
        Args:
            conn: Database connection
            command: Delete account command
            
        Returns:
            Result of account deletion
        """
        c = conn.cursor()
        # Get unread message count
        c.execute("SELECT COUNT(*) AS count FROM messages WHERE recipient = ? AND read = 0", 
                 (command["username"],))
        result = c.fetchone()
        unread_count = result["count"] if result else 0
        
        try:
            c.execute("DELETE FROM messages WHERE sender = ? OR recipient = ?", 
                     (command["username"], command["username"]))
            c.execute("DELETE FROM accounts WHERE username = ?", (command["username"],))
            conn.commit()
            return {"success": True, "message": f"Account deleted. Unread messages: {unread_count}"}
        except Exception as e:
            logger.error(f"Failed to delete account {command['username']}: {e}")
            return {"success": False, "message": "Failed to delete account."}
