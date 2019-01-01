#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, \
    jsonify, url_for, flash, make_response
from flask import session as login_session
from flask import send_from_directory

from werkzeug.utils import secure_filename

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from functools import wraps

from models import Base, Category, CatalogItem, CatalogItemImg, User

import httplib2
import json
import requests
import random
import string
import os
import uuid

UPLOAD_FOLDER = '/var/www/FlaskApp/FlaskApp/static'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLIENT_ID = json.loads(
    open('/var/www/FlaskApp/FlaskApp/client_secrets.json', 'r').read())['web']['client_id']

# Reusing the app name from previous project for authentication purposes
APPLICATION_NAME = "Restaurant Menu Application"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/catalog/item/imgs/JSON')
# JSON APIs to view all catalog item images
def catalogItemImgsJSON():
    imgs = session.query(CatalogItemImg).all()
    if imgs:
        return jsonify(catalogItemImgs=[i.serialize for i in imgs])
    return jsonify(catalogItemImgs=[])


@app.route('/catalog/<string:category_name>/<string:item_name>/imgs/JSON')
# JSON APIs to view catalog item images for specific category and catalog item
def categoryCatalogItemIdImgJSON(category_name, item_name):
    category = session.query(Category).filter_by(
        name=category_name).first()
    if category:
        item = session.query(CatalogItem).filter_by(
            name=item_name).first()
        if item:
            imgs = session.query(CatalogItemImg).filter_by(
                catalogItem_id=item.id).all()
            if imgs:
                return jsonify(catalogItemImgs=[i.serialize for i in imgs])
    return jsonify(catalogItemImgs=[])


@app.route('/catalog/item/JSON')
# JSON APIs to view all catalog items
def catalogItemsJSON():
    items = session.query(CatalogItem).all()
    if items:
        return jsonify(catalogItems=[i.serialize for i in items])
    return jsonify(catalogItems=[])


@app.route('/catalog/<int:category_id>/item/JSON')
# JSON APIs to view catalog items for specific category_id
def categoryIdItemJSON(category_id):
    items = session.query(CatalogItem).filter_by(
        category_id=category_id).all()
    if items:
        return jsonify(catalogItems=[i.serialize for i in items])
    return jsonify(catalogItems=[])


@app.route('/catalog/<string:category_name>/item/JSON')
# JSON APIs to view catalog items for specific category_name
def categoryNameItemJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        items = session.query(CatalogItem).filter_by(
            category_id=category.id).all()
        if items:
            return jsonify(catalogItems=[i.serialize for i in items])
    return jsonify(catalogItems=[])


@app.route('/catalog/<int:category_id>/item/<int:item_id>/JSON')
# JSON APIs to view specific catalog item data in category_id
def categoryIdItemIdJSON(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).first()
    if category:
        item = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(id=item_id).first()
        if item:
            return jsonify(catalog_Item=item.serialize)
    return jsonify(catalog_Item=[])


@app.route('/catalog/<string:category_name>/<string:item_title>/JSON')
# JSON APIs to view specific catalog item data in category_name
def categoryNameItemNameJSON(category_name, item_title):
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        item = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        if item:
            return jsonify(catalog_Item=item.serialize)
    return jsonify(catalog_Item=[])


@app.route('/catalog/JSON')
# JSON APIs to view all categories
def categoriesJSON():
    categories = session.query(Category).all()
    if categories:
        return jsonify(categories=[r.serialize for r in categories])
    return jsonify(categories=[])


@app.route('/catalog/<int:category_id>/JSON')
# JSON APIs to view specific category by id
def categoryIdJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).first()
    if category:
        return jsonify(category=category.serialize)
    return jsonify(category=[])


@app.route('/catalog/<string:category_name>/JSON')
# JSON APIs to view specific category by name
def categoryNameJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        return jsonify(category=category.serialize)
    return jsonify(category=[])


@app.route('/catalog/user/JSON')
# JSON APIs to view all users
def catalogUsersJSON():
    users = session.query(User).all()
    if users:
        return jsonify(users=[u.serialize for u in users])
    return jsonify(users=[])


@app.route('/catalog/user/<int:user_id>/JSON')
# JSON APIs to view specific user information
def catalogUserJSON(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        return jsonify(user=user.serialize)
    return jsonify(user=[])


# Decorator to be call by each new/edit/delete function to redirect user
# to log in if it is not logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash('In order to add/edit/delete, you must log in')
            return redirect(url_for('showCategories'))
    return decorated_function


def getCategories(items):
    # Create an array with category names which will be concatenated to the
    # catalog items listed in the main view
    categories_with_items = []
    for i in items:
        category = session.query(Category).filter_by(
            id=i.category_id).first()
        categories_with_items.append(category.name)
    return categories_with_items


@app.route('/catalog')
# Show all categories with the latest 10 catalog items added
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CatalogItem).order_by(
        CatalogItem.id.desc()).limit(10).all()
    # Get the category names which will be concatenated to each catalog item
    categories_with_items = getCategories(items=items)
    # Check if database is empty
    if not session.query(Category).first():
        flash('No categories found .. database empty')
        if 'username' not in login_session:
            flash('Users can add categories only if logged in .. \
                Please login ')
    # Categories will be listed on the first column of the table,
    # items will be concatenaded with categories_with_items and listed
    # in the second column
    return render_template(
        'catalog.html', categories=categories, items=items,
        categories_with_items=categories_with_items)


@app.route('/catalog/new', methods=['GET', 'POST'])
@login_required
# Create a new category
def newCategory():
    if request.method == 'POST':
        # Veriry that category name is not already in database
        name = request.form['name']
        if session.query(Category).filter_by(name=name).first():
            flash('Category name already exist .. record not added')
        else:
            newCategory = Category(
                name=request.form['name'],
                user_id=login_session['user_id'])
            session.add(newCategory)
            flash('New Category %s Successfully Created' % newCategory.name)
            session.commit()
    if request.method == 'GET':
        return render_template('newCategory.html')
    return redirect(url_for('showCategories'))


@app.route('/catalog/<category_name>/edit', methods=['GET', 'POST'])
@login_required
# Edit a catalog category
def editCategory(category_name):
    # Get the category to be edited
    editedCategory = session.query(Category).filter_by(
        name=category_name).first()
    if editedCategory:
        # If user is the owner then he is allowed to edit this item
        if editedCategory.user_id == login_session['user_id']:
            if request.method == 'POST':
                if request.form['name']:
                    # add the record only if the new name is not already
                    # in database
                    name = request.form['name']
                    if session.query(Category).filter(
                            id != editedCategory.id).filter_by(
                                name=name).first():
                        flash('Category name already exist .. \
                            record not updated')
                    else:
                        editedCategory.name = request.form['name']
                        session.commit()
                        flash(
                            'Category successfully edited %s'
                            % editedCategory.name)
            if request.method == 'GET':
                return render_template(
                    'editCategory.html',
                    category=editedCategory)
        # User is not the owner so it is not allowed to make any changes
        else:
            flash('You can not edit this category because \
                you are not the owner')
    else:
        flash('Category to edit was not found...')
    return redirect(url_for('showCategories'))


@app.route('/catalog/<category_name>/delete', methods=['GET', 'POST'])
@login_required
# Delete a category and its catalog items
def deleteCategory(category_name):
    # Get the category to be deleted
    categoryToDelete = session.query(Category).filter_by(
        name=category_name).first()
    if categoryToDelete:
        # If user is the owner then he is allowed to delete this item
        if categoryToDelete.user_id == login_session['user_id']:
            if request.method == 'POST':
                # Get the catalog items on this category so the images
                # can be deleted too
                items = session.query(CatalogItem).filter_by(
                    category_id=categoryToDelete.id).all()
                if items:
                    # Get the images on each catalog item and delete them
                    # from the file system
                    for i in items:
                        imgs = session.query(CatalogItemImg).filter_by(
                                catalogItem_id=i.id).all()
                        for img in imgs:
                            fileToRemove = os.path.join(
                                app.config['UPLOAD_FOLDER'],
                                img.uuid_prefix+img.name)
                            os.remove(fileToRemove)
                session.delete(categoryToDelete)
                session.commit()
                flash('%s Successfully Deleted' % categoryToDelete.name)
            if request.method == 'GET':
                return render_template(
                    'deleteCategory.html',
                    category=categoryToDelete)
        # User is not the owner so it is not allowed to make any changes
        else:
            flash('You can\'t delete this category because \
                you are not the owner')
    else:
        flash('Category to delete was not found...')
    return redirect(url_for('showCategories'))


@app.route('/catalog/<category_name>/<item_title>')
# Show specific catalog item details
def showCatalogItemDetails(category_name, item_title):
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        # Look for the item title in above category
        item = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        imgs = session.query(CatalogItemImg).filter_by(
            catalogItem_id=item.id).all()
        categories = session.query(Category)
        return render_template(
            'catalogItem.html', category_name=category_name,
            item=item, categories=categories, imgs=imgs)
    else:
        flash('Category was found...')
        return redirect(url_for('showCategories'))


@app.route('/catalog/<category_name>')
# Show catalog items for a specific category
def showCatalogItem(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        items = session.query(CatalogItem).filter_by(
            category_id=category.id).all()
        return render_template(
            'categoryCatalogItem.html', items=items, category=category)
    else:
        flash('Category was not found...')
        return redirect(url_for('showCategories'))


@app.route('/catalog/item/new', methods=['GET', 'POST'])
@login_required
# Create a new catalog item
def newCatalogItem():
    categories = session.query(Category)
    if categories:
        if request.method == 'POST':
            category = session.query(Category).filter_by(
                name=request.form['category']).first()
            if category:
                # Add a new item only if title does not exist
                if session.query(CatalogItem).filter_by(
                        category_id=category.id).filter_by(
                        title=request.form['title']).first():
                    flash('Catalog item description already exist in this \
                        category.. record not updated')
                    return redirect(url_for(
                        'showCatalogItem',
                        category_name=category.name))
                else:
                    newItem = CatalogItem(
                        title=request.form['title'],
                        description=request.form['description'],
                        category_id=category.id,
                        user_id=login_session['user_id'])
                    session.add(newItem)
                    session.commit()
                    flash(
                        'New Catalog Item: %s Successfully Created'
                        % (newItem.title))
                    return redirect(url_for(
                        'showCatalogItemDetails',
                        category_name=category.name,
                        item_title=newItem.title))
            else:
                flash('Category was not found...')
        if request.method == 'GET':
            return render_template(
                'newCatalogItem.html',
                categories=categories)
    else:
        flash('No categories found...')
    return redirect(url_for('showCategories'))


@app.route(
    '/catalog/<category_name>/<item_title>/edit',
    methods=['GET', 'POST'])
@login_required
# Edit a catalog item
def editCatalogItem(category_name, item_title):
    # Get the catalog item to be edited
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        editedItem = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        # Get the categories so they are displayed in a list of options
        if editedItem:
            categories = session.query(Category)
            if categories:
                # If user is the owner then he is allowed to edit this item
                if editedItem.user_id == login_session['user_id']:
                    imgs = session.query(CatalogItemImg).filter_by(
                        catalogItem_id=editedItem.id).all()
                    if request.method == 'POST':
                        if request.form['category']:
                            category = session.query(Category).filter_by(
                                name=request.form['category']).first()
                        # Edit item only if title is not already in database
                        if session.query(CatalogItem).filter_by(
                                category_id=category.id).filter(
                                id != editedItem.id).filter_by(
                                title=request.form['title']).first():
                            flash('Catalog item title already exist in this \
                                category.. record not updated')
                            return redirect(url_for(
                                'showCatalogItem',
                                category_name=category.name))
                        else:
                            if request.form['title']:
                                editedItem.title = request.form['title']
                            if request.form['description']:
                                editedItem.description = request.form[
                                    'description']
                            if request.form['category']:
                                editedItem.category_id = category.id
                            session.add(editedItem)
                            session.commit()
                            flash(
                                'Catalog Item %s Successfully Edited'
                                % (editedItem.title))
                            return redirect(url_for(
                                'showCatalogItemDetails',
                                category_name=category.name,
                                item_title=editedItem.title))
                    if request.method == 'GET':
                        return render_template(
                            'editCatalogItem.html',
                            category_name=category_name,
                            item_title=item_title,
                            item=editedItem,
                            categories=categories,
                            imgs=imgs)
                # User is not the owner so it is not allowed
                # to make any changes
                else:
                    flash('You can\'t edit this item because \
                        you are not the owner')
            else:
                flash('No categories found...')
        else:
            flash('Item to edit was not found...')
    else:
        flash('Category was not found...')
    return redirect(url_for('showCategories'))


@app.route(
    '/catalog/<category_name>/<item_title>/delete',
    methods=['GET', 'POST'])
@login_required
# Delete a catalog item
def deleteCatalogItem(category_name, item_title):
    # Get the catalog item to be deleted
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        itemToDelete = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        if itemToDelete:
            # Get the categories so they are displayed in a list of options
            categories = session.query(Category)
            if categories:
                # If user is the owner then he is allowed to delete this item
                if itemToDelete.user_id == login_session['user_id']:
                    imgs = session.query(CatalogItemImg).filter_by(
                        catalogItem_id=itemToDelete.id).all()
                    if request.method == 'POST':
                        # Delete the actual image files
                        for img in imgs:
                            fileToRemove = os.path.join(
                                app.config['UPLOAD_FOLDER'],
                                img.uuid_prefix+img.name)
                            os.remove(fileToRemove)
                        session.delete(itemToDelete)
                        session.commit()
                        flash('Catalog Item and images Successfully Deleted')
                        return redirect(url_for(
                            'showCatalogItem',
                            category_name=category.name))
                    if request.method == 'GET':
                        return render_template(
                            'deleteCatalogItem.html',
                            category_name=category_name,
                            item=itemToDelete,
                            categories=categories,
                            imgs=imgs)
                # User is not the owner so it is not allowed
                # to make any changes
                else:
                    flash('You can\'t delete this item because \
                        you are not the owner')
            else:
                flash('No categories found...')
        else:
            flash('Item to delete was not found...')
    else:
        flash('Category was not found...')
    return redirect(url_for('showCategories'))


@app.route('/uploads/<filename>')
# Used to upload a catalog item image to the specific directory
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# Used to check if the extension of the file name for the catalog item image
# is in the list of allowed extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route(
    '/catalog/<category_name>/<item_title>/img',
    methods=['GET', 'POST'])
# Display catalog item images
def catalogItemImage(category_name, item_title):
    # Get the category
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        # Get the catalog item
        item = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        if item:
            # Get the images for this catalog item
            imgs = session.query(CatalogItemImg).filter_by(
                catalogItem_id=item.id).all()
            if imgs:
                return render_template(
                    'catalogItemImage.html',
                    category_name=category_name,
                    item_title=item_title,
                    imgs=imgs)
            else:
                flash('Images were not found...')
        else:
            flash('Catalog item was not found...')
    else:
        flash('Category was not found...')
    return redirect(url_for('showCategories'))


@app.route(
    '/catalog/<category_name>/<item_title>/img/new',
    methods=['GET', 'POST'])
@login_required
# Add a new catalog item image
def newCatalogItemImage(category_name, item_title):
    # Get the category
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        # Get the catalog item
        item = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        if item:
            if item.user_id == login_session['user_id']:
                if request.method == 'POST':
                    if 'file' not in request.files:
                        flash('No file part for catalog item image')
                    else:
                        file = request.files['file']
                        # if user does not select file, browser also
                        # submit a empty part without filename
                        if file.filename == '':
                            flash('No selected file for catalog item image')
                        elif file and allowed_file(file.filename):
                            if session.query(CatalogItemImg).filter_by(
                                    catalogItem_id=item.id).filter_by(
                                    name=file.filename).first():
                                flash('Catalog item image name already exist\
                                    in this catalog item.. chose a different\
                                    file')
                            else:
                                filename = secure_filename(file.filename)
                                fileNamePrefix = str(uuid.uuid4())
                                file.save(os.path.join(
                                    app.config['UPLOAD_FOLDER'],
                                    fileNamePrefix+filename))
                                newImage = CatalogItemImg(
                                    name=file.filename,
                                    uuid_prefix=fileNamePrefix,
                                    catalogItem_id=item.id,
                                    user_id=item.user_id
                                )
                                session.add(newImage)
                                session.commit()
                                flash(
                                    'New Catalog Item Image: %s Successfully\
                                    Created' % (newImage.name))
                                categories = session.query(Category)
                                imgs = session.query(CatalogItemImg).filter_by(
                                    catalogItem_id=item.id).all()
                        else:
                            flash(
                                'File extension is not in the list of \
                                allowed extensions: '
                                + ', '.join(ALLOWED_EXTENSIONS))
                    return redirect(url_for(
                        'catalogItemImage',
                        category_name=category_name,
                        item_title=item_title))
                if request.method == 'GET':
                    return render_template(
                        'newCatalogItemImage.html',
                        category_name=category_name,
                        item_title=item_title)
            # User is not the owner so it is not allowed
            # to make any changes
            else:
                flash('You can\'t add images to this catalog item because \
                    you are not the owner')
        else:
            flash('Catalog item to edit was not found...')
    else:
        flash('Category was not found...')
    return redirect(url_for('showCategories'))


@app.route(
    '/catalog/<category_name>/<item_title>/<img_name>/edit',
    methods=['GET', 'POST'])
@login_required
# Add a new catalog item image
def editCatalogItemImage(category_name, item_title, img_name):
    # Get the category
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        # Get the catalog item
        item = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        if item:
            imgToUpdate = session.query(CatalogItemImg).filter_by(
                catalogItem_id=item.id).filter_by(
                    name=img_name).first()
            if imgToUpdate:
                if imgToUpdate.user_id == login_session['user_id']:
                    if request.method == 'POST':
                        if 'file' not in request.files:
                            flash('No file part for catalog item image')
                        else:
                            file = request.files['file']
                            # if user does not select file, browser also
                            # submit a empty part without filename
                            if file.filename == '':
                                flash('No selected file for catalog item \
                                    image')
                            elif file and allowed_file(file.filename):
                                if session.query(CatalogItemImg).filter_by(
                                        catalogItem_id=item.id).filter_by(
                                        name=file.filename).first():
                                    flash('Catalog item image name already \
                                        exist in this catalog item.. chose \
                                        a different file')
                                else:
                                    filename = secure_filename(file.filename)
                                    fileNamePrefix = str(uuid.uuid4())
                                    file.save(os.path.join(
                                        app.config['UPLOAD_FOLDER'],
                                        fileNamePrefix+filename))
                                    fileToRemove = os.path.join(
                                        app.config['UPLOAD_FOLDER'],
                                        imgToUpdate.uuid_prefix
                                        + imgToUpdate.name)
                                    os.remove(fileToRemove)
                                    imgToUpdate.name = filename
                                    imgToUpdate.uuid_prefix = fileNamePrefix
                                    session.add(imgToUpdate)
                                    session.commit()
                                    flash(
                                        'Catalog Item Image: %s Successfully\
                                        Updated' % (imgToUpdate.name))
                            else:
                                flash(
                                    'File extension is not in the list of\
                                    allowed extensions: '
                                    + ', '.join(ALLOWED_EXTENSIONS))
                        return redirect(url_for(
                            'catalogItemImage',
                            category_name=category_name,
                            item_title=item_title))
                    if request.method == 'GET':
                        return render_template(
                            'editCatalogItemImage.html',
                            category_name=category_name,
                            item_title=item_title,
                            img_name=img_name)
                # User is not the owner so it is not allowed
                # to make any changes
                else:
                    flash('You can\'t update images on this catalog item\
                        because you are not the owner')
            else:
                flash('Image was not found...')
        else:
            flash('Catalog item to edit was not found...')
    else:
        flash('Category was not found...')
    return redirect(url_for('showCategories'))


@app.route(
    '/catalog/<category_name>/<item_title>/<img_name>/delete',
    methods=['GET', 'POST'])
@login_required
# Delete a catalog item image
def deleteCatalogItemImage(category_name, item_title, img_name):
    # Get the category
    category = session.query(Category).filter_by(name=category_name).first()
    if category:
        # Get the catalog item
        item = session.query(CatalogItem).filter_by(
            category_id=category.id).filter_by(title=item_title).first()
        if item:
            # Get the image for this catalog item
            img = session.query(CatalogItemImg).filter_by(
                catalogItem_id=item.id).filter_by(name=img_name).first()
            if img:
                if item.user_id == login_session['user_id']:
                    if request.method == 'POST':
                        fileToRemove = os.path.join(
                            app.config['UPLOAD_FOLDER'],
                            img.uuid_prefix+img.name)
                        print fileToRemove
                        os.remove(fileToRemove)
                        session.delete(img)
                        session.commit()
                        flash(
                            'Catalog Item Image: %s Successfully deleted'
                            % (img.name))
                        return redirect(url_for(
                            'showCatalogItemDetails',
                            category_name=category_name,
                            item_title=item_title))
                    if request.method == 'GET':
                        return render_template(
                            'deleteCatalogItemImage.html',
                            category_name=category_name,
                            item_title=item_title,
                            img_name=img_name,
                            img=img)
                # User is not the owner so it is not allowed
                # to make any changes
                else:
                    flash('You can\'t add images to this catalog item because \
                        you are not the owner')
            else:
                flash('Image was not found...')
        else:
            flash('Catalog item to edit was not found...')
    else:
        flash('Category was not found...')
    return redirect(url_for('showCategories'))


@app.route('/login')
# Create anti-forgery state token to login user with a third party system
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html',  STATE=state)


@app.route('/fbconnect', methods=['POST'])
# Log in user using facebook
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=\
        fb_exchange_token&client_id=%s&client_secret=%s\
        &fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange
        we have to split the token first on commas and select the first index
        which gives us the key : value for the server access token then we
        split it on colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used directly in the
        graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')
    url = 'https://graph.facebook.com/v2.8/me?access_token=%s\
        &fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to
    # properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s\
        &redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # See if user exists
    user_id = getUserID(login_session['email'])
    # If user does not exist in database then it is inserted
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src = "'
    output += login_session['picture']
    output += ' " style="width: 300px; height: 300px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
# Logout from facebook
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
        % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
# Log in using google
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # See if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    # If user does not exist then insert it to the database
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src = "'
    output += login_session['picture']
    output += ' " style="width: 300px; height: 300px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    # add user to the database
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one_or_none()
    return user.id


def getUserID(email):
    # get user_id based on its email for authentication purposes
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            return user.id
    except exc.DBAPIError as err:
        print "Error: %s" % err
        return None


@app.route('/gdisconnect')
# disconnect from google
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
                json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
# Disconnect based on provider
def disconnect():
    # if provider then users is logged in
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            # this data is not deleted in above function
            del login_session['facebook_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
