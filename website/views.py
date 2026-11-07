from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .models import create_note, delete_note, get_note, get_notes, update_note

views = Blueprint("views", __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '')

        if not title or not content.strip():
            flash('Please fill in all fields.', 'error')
        elif create_note(current_user.id, title, content):
            flash('Note created successfully!', 'success')
            return redirect(url_for('views.home'))
        else:
            flash('Failed to create note.', 'error')

    notes = get_notes(current_user.id)
    if notes is None:
        flash('Could not load your notes from the database.', 'error')
        notes = []

    return render_template("home.html", notes=notes)


@views.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '')

        if not title or not content.strip():
            flash('Please fill in all fields.', 'error')
        else:
            if create_note(current_user.id, title, content):
                flash('Note created successfully!', 'success')
            else:
                flash('Failed to create note.', 'error')

    return redirect(url_for('views.home'))


@views.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = get_note(current_user.id, note_id)
    if note is None:
        flash('Note not found.', 'error')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '')

        if not title or not content.strip():
            flash('Please fill in all fields.', 'error')
        elif update_note(current_user.id, note_id, title, content):
            flash('Note updated successfully!', 'success')
            return redirect(url_for('views.home'))
        else:
            flash('Failed to update note.', 'error')

        note['title'] = title
        note['content'] = content

    return render_template('edit_note.html', note=note)


@views.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def remove_note(note_id):
    if delete_note(current_user.id, note_id):
        flash('Note deleted successfully.', 'success')
    else:
        flash('Note could not be deleted.', 'error')

    return redirect(url_for('views.home'))
