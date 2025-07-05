#!/usr/bin/env python3

import sqlite3
import json
import datetime
import os
import shutil
import subprocess
import tarfile
import base64
from pathlib import Path

def extract_complete_backup():
    """Extract complete Gogs state including repository code/content"""
    
    print("🚀 Starting COMPLETE Gogs backup (metadata + code)...")
    
    db_path = "/gogs/data/gogs.db"
    repos_path = "/home/git/gogs-repositories"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        backup_data = {
            "backup_timestamp": datetime.datetime.now().isoformat(),
            "backup_method": "complete_database_and_git",
            "metadata": {
                "users": [],
                "repositories": [],
                "issues": [],
                "stats": {}
            },
            "repository_contents": {},
            "file_attachments": {}
        }
        
        # Extract metadata (same as before but more organized)
        print("📊 Extracting metadata...")
        backup_data["metadata"] = extract_metadata(conn)
        
        # Extract actual Git repositories
        print("📦 Extracting Git repositories...")
        backup_data["repository_contents"] = extract_git_repositories(repos_path)
        
        # Extract file attachments if any
        print("📎 Extracting file attachments...")
        backup_data["file_attachments"] = extract_attachments()
        
        # Save complete backup
        output_file = "/complete_backup.json"
        with open(output_file, 'w') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Also create a compressed backup
        create_compressed_backup(backup_data)
        
        print_backup_summary(backup_data)
        
        conn.close()
        return backup_data
        
    except Exception as e:
        print(f"❌ Error creating complete backup: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_metadata(conn):
    """Extract all metadata from database"""
    metadata = {"users": [], "repositories": [], "issues": [], "stats": {}}
    
    # Users
    print("   👥 Extracting users...")
    cursor = conn.execute("""
        SELECT id, name, full_name, email, type, location, website,
               is_active, is_admin, num_followers, num_following, 
               num_stars, num_repos, description, created_unix, updated_unix
        FROM user ORDER BY id
    """)
    
    for row in cursor.fetchall():
        user = {
            "id": row["id"],
            "username": row["name"],
            "full_name": row["full_name"] or "",
            "email": row["email"],
            "type": "admin" if row["is_admin"] else "user",
            "location": row["location"] or "",
            "website": row["website"] or "",
            "is_active": bool(row["is_active"]),
            "is_admin": bool(row["is_admin"]),
            "stats": {
                "followers": row["num_followers"] or 0,
                "following": row["num_following"] or 0,
                "stars": row["num_stars"] or 0,
                "repositories": row["num_repos"] or 0
            },
            "description": row["description"] or "",
            "created_at": datetime.datetime.fromtimestamp(row["created_unix"]).isoformat() if row["created_unix"] else None,
            "updated_at": datetime.datetime.fromtimestamp(row["updated_unix"]).isoformat() if row["updated_unix"] else None
        }
        metadata["users"].append(user)
    
    # Repositories
    print("   📦 Extracting repository metadata...")
    cursor = conn.execute("""
        SELECT r.id, r.owner_id, r.name, r.description, r.website, r.default_branch,
               r.size, r.num_watches, r.num_stars, r.num_forks, r.num_issues,
               r.num_closed_issues, r.num_pulls, r.num_closed_pulls,
               r.is_private, r.is_bare, r.is_mirror, r.is_fork, r.fork_id,
               r.enable_wiki, r.enable_issues, r.enable_pulls,
               r.created_unix, r.updated_unix,
               u.name as owner_name
        FROM repository r
        JOIN user u ON r.owner_id = u.id
        ORDER BY r.id
    """)
    
    for row in cursor.fetchall():
        repo = {
            "id": row["id"],
            "name": row["name"],
            "full_name": f"{row['owner_name']}/{row['name']}",
            "description": row["description"] or "",
            "website": row["website"] or "",
            "default_branch": row["default_branch"] or "master",
            "owner": {
                "id": row["owner_id"],
                "username": row["owner_name"]
            },
            "private": bool(row["is_private"]),
            "fork": bool(row["is_fork"]),
            "mirror": bool(row["is_mirror"]),
            "bare": bool(row["is_bare"]),
            "size": row["size"] or 0,
            "stats": {
                "watchers": row["num_watches"] or 0,
                "stars": row["num_stars"] or 0,
                "forks": row["num_forks"] or 0,
                "open_issues": row["num_issues"] or 0,
                "closed_issues": row["num_closed_issues"] or 0,
                "open_pulls": row["num_pulls"] or 0,
                "closed_pulls": row["num_closed_pulls"] or 0
            },
            "features": {
                "wiki_enabled": bool(row["enable_wiki"]),
                "issues_enabled": bool(row["enable_issues"]),
                "pulls_enabled": bool(row["enable_pulls"])
            },
            "fork_info": {
                "is_fork": bool(row["is_fork"]),
                "parent_id": row["fork_id"] if row["is_fork"] else None
            },
            "created_at": datetime.datetime.fromtimestamp(row["created_unix"]).isoformat() if row["created_unix"] else None,
            "updated_at": datetime.datetime.fromtimestamp(row["updated_unix"]).isoformat() if row["updated_unix"] else None
        }
        metadata["repositories"].append(repo)
    
    # Issues
    print("   🐛 Extracting issues...")
    cursor = conn.execute("""
        SELECT i.id, i.repo_id, i."index", i.poster_id, i.name as title, i.content,
               i.milestone_id, i.priority, i.assignee_id, i.is_closed, i.is_pull,
               i.num_comments, i.deadline_unix, i.created_unix, i.updated_unix,
               r.name as repo_name, ru.name as repo_owner,
               pu.name as poster_name, pu.email as poster_email,
               au.name as assignee_name
        FROM issue i
        JOIN repository r ON i.repo_id = r.id
        JOIN user ru ON r.owner_id = ru.id
        JOIN user pu ON i.poster_id = pu.id
        LEFT JOIN user au ON i.assignee_id = au.id
        ORDER BY i.id
    """)
    
    for row in cursor.fetchall():
        issue = {
            "id": row["id"],
            "number": row["index"],
            "title": row["title"] or "",
            "body": row["content"] or "",
            "state": "closed" if row["is_closed"] else "open",
            "is_pull_request": bool(row["is_pull"]),
            "repository": {
                "id": row["repo_id"],
                "name": row["repo_name"],
                "owner": row["repo_owner"],
                "full_name": f"{row['repo_owner']}/{row['repo_name']}"
            },
            "user": {
                "id": row["poster_id"],
                "username": row["poster_name"],
                "email": row["poster_email"]
            },
            "assignee": {
                "id": row["assignee_id"],
                "username": row["assignee_name"]
            } if row["assignee_id"] else None,
            "milestone_id": row["milestone_id"],
            "priority": row["priority"] or 0,
            "comments_count": row["num_comments"] or 0,
            "deadline": datetime.datetime.fromtimestamp(row["deadline_unix"]).isoformat() if row["deadline_unix"] else None,
            "created_at": datetime.datetime.fromtimestamp(row["created_unix"]).isoformat() if row["created_unix"] else None,
            "updated_at": datetime.datetime.fromtimestamp(row["updated_unix"]).isoformat() if row["updated_unix"] else None
        }
        metadata["issues"].append(issue)
    
    # Stats
    metadata["stats"] = {
        "total_users": len(metadata["users"]),
        "admin_users": len([u for u in metadata["users"] if u["is_admin"]]),
        "active_users": len([u for u in metadata["users"] if u["is_active"]]),
        "total_repositories": len(metadata["repositories"]),
        "public_repositories": len([r for r in metadata["repositories"] if not r["private"]]),
        "private_repositories": len([r for r in metadata["repositories"] if r["private"]]),
        "fork_repositories": len([r for r in metadata["repositories"] if r["fork"]]),
        "mirror_repositories": len([r for r in metadata["repositories"] if r["mirror"]]),
        "total_issues": len(metadata["issues"]),
        "open_issues": len([i for i in metadata["issues"] if i["state"] == "open" and not i["is_pull_request"]]),
        "closed_issues": len([i for i in metadata["issues"] if i["state"] == "closed" and not i["is_pull_request"]]),
        "pull_requests": len([i for i in metadata["issues"] if i["is_pull_request"]])
    }
    
    return metadata

def extract_git_repositories(repos_path):
    """Extract actual Git repository contents"""
    repository_contents = {}
    
    if not os.path.exists(repos_path):
        print(f"   ⚠️  Repository path not found: {repos_path}")
        return repository_contents
    
    try:
        # Find all .git directories (bare repositories)
        for root, dirs, files in os.walk(repos_path):
            for dir_name in dirs:
                if dir_name.endswith('.git'):
                    repo_path = os.path.join(root, dir_name)
                    relative_path = os.path.relpath(repo_path, repos_path)
                    
                    print(f"   📦 Processing repository: {relative_path}")
                    
                    repo_data = extract_single_repository(repo_path, relative_path)
                    if repo_data:
                        repository_contents[relative_path] = repo_data
    
    except Exception as e:
        print(f"   ❌ Error extracting repositories: {e}")
    
    return repository_contents

def extract_single_repository(repo_path, repo_name):
    """Extract a single Git repository's contents"""
    try:
        repo_data = {
            "path": repo_name,
            "type": "git_bare_repository",
            "branches": {},
            "tags": [],
            "refs": {},
            "config": {},
            "archive": None
        }
        
        # Check if it's a bare repository
        if os.path.exists(os.path.join(repo_path, "HEAD")):
            # Get branches
            try:
                result = subprocess.run(
                    ["git", "--git-dir", repo_path, "branch", "-a"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    branches = [line.strip().lstrip('* ') for line in result.stdout.split('\n') if line.strip()]
                    repo_data["branches"] = {"list": branches, "count": len(branches)}
            except subprocess.TimeoutExpired:
                print(f"      ⚠️  Timeout getting branches for {repo_name}")
            except Exception as e:
                print(f"      ⚠️  Error getting branches for {repo_name}: {e}")
            
            # Get tags
            try:
                result = subprocess.run(
                    ["git", "--git-dir", repo_path, "tag", "-l"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    tags = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                    repo_data["tags"] = tags
            except Exception as e:
                print(f"      ⚠️  Error getting tags for {repo_name}: {e}")
            
            # Get latest commit info
            try:
                result = subprocess.run(
                    ["git", "--git-dir", repo_path, "log", "-1", "--pretty=format:%H|%an|%ae|%ad|%s"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    commit_parts = result.stdout.strip().split('|')
                    if len(commit_parts) >= 5:
                        repo_data["latest_commit"] = {
                            "hash": commit_parts[0],
                            "author_name": commit_parts[1],
                            "author_email": commit_parts[2],
                            "date": commit_parts[3],
                            "message": commit_parts[4]
                        }
            except Exception as e:
                print(f"      ⚠️  Error getting latest commit for {repo_name}: {e}")
            
            # Create a tar archive of the repository
            try:
                archive_path = f"/tmp/{repo_name.replace('/', '_')}.tar.gz"
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(repo_path, arcname=os.path.basename(repo_name))
                
                # Encode as base64 for JSON storage
                with open(archive_path, "rb") as f:
                    repo_data["archive"] = base64.b64encode(f.read()).decode('utf-8')
                
                # Clean up temp file
                os.remove(archive_path)
                
                print(f"      ✅ Archived repository {repo_name} ({len(repo_data['archive'])} chars)")
                
            except Exception as e:
                print(f"      ⚠️  Error creating archive for {repo_name}: {e}")
        
        return repo_data
        
    except Exception as e:
        print(f"   ❌ Error processing repository {repo_name}: {e}")
        return None

def extract_attachments():
    """Extract file attachments if any exist"""
    attachments = {}
    
    # Gogs typically stores attachments in /gogs/data/attachments
    attachments_path = "/gogs/data/attachments"
    
    if os.path.exists(attachments_path):
        try:
            for root, dirs, files in os.walk(attachments_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, attachments_path)
                    
                    try:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            attachments[relative_path] = {
                                "filename": file_name,
                                "size": len(file_data),
                                "content": base64.b64encode(file_data).decode('utf-8')
                            }
                    except Exception as e:
                        print(f"   ⚠️  Error reading attachment {relative_path}: {e}")
        except Exception as e:
            print(f"   ⚠️  Error processing attachments: {e}")
    
    return attachments

def create_compressed_backup(backup_data):
    """Create a compressed version of the backup"""
    try:
        # Create a tar.gz file with all backup components
        with tarfile.open("/complete_backup.tar.gz", "w:gz") as tar:
            # Add JSON metadata
            json_path = "/complete_backup.json"
            if os.path.exists(json_path):
                tar.add(json_path, arcname="backup_metadata.json")
            
            # Add repository archives (if they exist as separate files)
            repos_backup_path = "/gogs-repositories"
            if os.path.exists(repos_backup_path):
                tar.add(repos_backup_path, arcname="repositories")
            
            # Add database
            db_path = "/gogs/data/gogs.db"
            if os.path.exists(db_path):
                tar.add(db_path, arcname="gogs.db")
            
            # Add configuration
            config_path = "/gogs/custom/conf/app.ini"
            if os.path.exists(config_path):
                tar.add(config_path, arcname="app.ini")
        
        print("   📦 Created compressed backup: /complete_backup.tar.gz")
        
    except Exception as e:
        print(f"   ⚠️  Error creating compressed backup: {e}")

def print_backup_summary(backup_data):
    """Print a summary of the backup"""
    metadata = backup_data["metadata"]
    
    print(f"\n✅ COMPLETE backup created successfully!")
    print(f"📁 JSON backup: /complete_backup.json")
    print(f"📦 Compressed backup: /complete_backup.tar.gz")
    
    print(f"\n📊 Backup Summary:")
    print(f"   👥 Users: {metadata['stats']['total_users']} ({metadata['stats']['admin_users']} admins)")
    print(f"   📦 Repositories: {metadata['stats']['total_repositories']} ({metadata['stats']['public_repositories']} public)")
    print(f"   🐛 Issues: {metadata['stats']['total_issues']} ({metadata['stats']['open_issues']} open)")
    print(f"   📎 Repository Archives: {len(backup_data['repository_contents'])} repos with code")
    print(f"   📎 File Attachments: {len(backup_data['file_attachments'])} files")
    
    print(f"\n📦 Repository Code Backup:")
    for repo_path, repo_data in backup_data["repository_contents"].items():
        branches = repo_data.get("branches", {}).get("count", 0)
        tags = len(repo_data.get("tags", []))
        archived = "✅" if repo_data.get("archive") else "❌"
        print(f"   {archived} {repo_path} - {branches} branches, {tags} tags")

if __name__ == "__main__":
    extract_complete_backup()
