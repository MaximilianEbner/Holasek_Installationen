from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, PositionTemplate, PositionTemplateSubItem

templates_admin = Blueprint('templates_admin', __name__)

# List all templates
@templates_admin.route('/admin/templates')
def list_templates():
    templates = PositionTemplate.query.all()
    return render_template('admin/list_templates.html', templates=templates)

# Add new template
@templates_admin.route('/admin/templates/add', methods=['GET', 'POST'])
def add_template():
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('Name erforderlich', 'danger')
            return redirect(url_for('templates_admin.add_template'))
        template = PositionTemplate(name=name)
        db.session.add(template)
        db.session.commit()
        flash('Vorlage hinzugefügt', 'success')
        return redirect(url_for('templates_admin.edit_template', template_id=template.id))
    return render_template('admin/add_template.html')

# Edit template and its subitems
@templates_admin.route('/admin/templates/<int:template_id>/edit', methods=['GET', 'POST'])
def edit_template(template_id):
    template = PositionTemplate.query.get_or_404(template_id)
    if request.method == 'POST':
        template.name = request.form.get('name')
        db.session.commit()
        flash('Vorlage gespeichert', 'success')
        return redirect(url_for('templates_admin.list_templates'))
    return render_template('admin/edit_template.html', template=template)

# Delete template
@templates_admin.route('/admin/templates/<int:template_id>/delete', methods=['POST'])
def delete_template(template_id):
    template = PositionTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    flash('Vorlage gelöscht', 'success')
    return redirect(url_for('templates_admin.list_templates'))

# Add subitem to template
@templates_admin.route('/admin/templates/<int:template_id>/add_subitem', methods=['POST'])
def add_subitem(template_id):
    template = PositionTemplate.query.get_or_404(template_id)
    description = request.form.get('description')
    item_type = request.form.get('item_type')
    unit = request.form.get('unit')
    price_per_unit = request.form.get('price_per_unit')
    formula = request.form.get('formula')
    subitem = PositionTemplateSubItem(
        template_id=template.id,
        description=description,
        item_type=item_type,
        unit=unit,
        price_per_unit=price_per_unit,
        formula=formula
    )
    db.session.add(subitem)
    db.session.commit()
    flash('Unterposition hinzugefügt', 'success')
    return redirect(url_for('templates_admin.edit_template', template_id=template.id))

# Delete subitem
@templates_admin.route('/admin/templates/<int:template_id>/delete_subitem/<int:subitem_id>', methods=['POST'])
def delete_subitem(template_id, subitem_id):
    subitem = PositionTemplateSubItem.query.get_or_404(subitem_id)
    db.session.delete(subitem)
    db.session.commit()
    flash('Unterposition gelöscht', 'success')
    return redirect(url_for('templates_admin.edit_template', template_id=template_id))
