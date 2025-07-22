# 🚀 Deployment Guide - GitHub & Railway

## ✅ FILES TO UPLOAD TO GITHUB:

### Core Application Files:
- `app.py` - Main Flask application
- `config.py` - Configuration (with environment variables)
- `models.py` - Database models
- `forms.py` - WTForms
- `utils.py` - Utility functions
- `work_steps.py` - Work steps logic
- `invoice_pdf.py` - PDF generation
- `pdf_export.py` - PDF export functionality

### Database & Migration:
- `init_db.py` - Database initialization
- `migrations/` - Database migration files
- All `.py` files in migrations/

### Templates & Static Files:
- `templates/` - All HTML templates
- `static/` - CSS, JS, images (except uploads)
- `templates_excel/` - Excel templates

### Configuration Files:
- `requirements.txt` - Python dependencies
- `Procfile` - Railway deployment config
- `runtime.txt` - Python version
- `.gitignore` - Git ignore rules
- `README.txt` - Documentation

### Helper Scripts:
- `create_default_templates.py`
- `templates_admin.py`
- `init_acquisition_channels.py`
- `check_model.py`
- `check_template.py`
- All other `.py` admin/utility scripts

## ❌ FILES NOT TO UPLOAD:

### Local Development:
- `START_APP.bat` - Local start script
- `INSTALLATION_PACKAGE.bat` - Local installation
- `BENUTZERHANDBUCH.txt` - Local user manual

### Database & Data:
- `instance/` - Local database folder
- `*.db` - SQLite database files
- `backup_*/` - Backup folders
- `csv_backup_*/` - CSV backup folders

### Cache & Temporary:
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python files
- `temp_pdfs/` - Temporary PDF files

### User Data:
- `static/uploads/` - User uploaded files
- `*.pdf` - Sample/user PDF files
- `Anzahlung-*.pdf` - Sample invoices
- `Rechnung-*.pdf` - Sample invoices

### IDE & OS:
- `.vscode/` - VS Code settings
- `.idea/` - PyCharm settings
- `.DS_Store` - macOS files
- `Thumbs.db` - Windows thumbnails

## 🔧 RAILWAY DEPLOYMENT STEPS:

### 1. Prepare Repository:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Railway Setup:
1. Connect GitHub repository to Railway
2. Set environment variables:
   - `SECRET_KEY`: Generate strong secret key
   - `DATABASE_URL`: Will be auto-provided by Railway
3. Deploy automatically

### 3. Environment Variables for Railway:
```
SECRET_KEY=your-super-secret-key-here-min-32-chars
DATABASE_URL=postgresql://... (auto-generated)
FLASK_ENV=production
```

### 4. Post-Deployment:
1. Check logs for any errors
2. Test database initialization
3. Create first admin user
4. Test all major functions

## 🗂️ FILE SUMMARY:

**Upload to GitHub:** ~50 files
- All Python source code
- All templates and static assets
- Configuration files
- Documentation

**Keep Local Only:** ~30+ files
- Local development tools
- User data and databases
- Temporary/cache files
- OS-specific files

## ⚠️ IMPORTANT NOTES:

### Security:
- Never upload database files with real data
- Use environment variables for secrets
- Change default admin password immediately

### Database:
- Railway will create PostgreSQL database automatically
- SQLite files are for local development only
- Migration files should be included

### Static Files:
- Include template images (innSAN_Logo.png/svg)
- Exclude user uploads and temporary files
- Keep example templates

Ready for deployment! 🚀
