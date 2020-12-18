from flask import render_template,request,redirect,url_for,abort,flash
from . import main
from .forms import UpdateProfile,BlogForm,CommentForm, SubscriberForm
from .. import db, photos
from ..models import User, Comment, Blog,Subscriber,Article
from flask_login import login_required, current_user
from ..email import mail_message

# Views
@main.route('/')
def index():
    '''
    View root page function that returns the index page and its data
    '''

    title= 'Home'
    return render_template('index.html',title = title)

@main.route('/user/<uname>')
def profile(uname):
    # articles=Article.get_all_articles
    articles=Article.query.all()
    
    user = User.query.filter_by(username = uname).first()
    
    print(articles)

    if user is None:
        abort(404)

    return render_template("profile/profile.html", user = user,articles=articles)
@main.route('/user/<uname>/update',methods = ['GET','POST'])
@login_required
def update_profile(uname):
    user = User.query.filter_by(username = uname).first()
    if user is None:
        abort(404)

    form = UpdateProfile()

    if form.validate_on_submit():
        user.bio = form.bio.data

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('.profile',uname=user.username))

    return render_template('profile/update.html',form = form)

@main.route('/user/<uname>/update/pic',methods= ['POST'])
@login_required
def update_pic(uname):
    user = User.query.filter_by(username = uname).first()
    if 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        path = f'photos/{filename}'
        user.profile_pic_path = path
        db.session.commit()
    return redirect(url_for('main.profile',uname=uname))

@main.route('/blogs/new', methods=['GET', 'POST'])
@login_required
def blogs():
    """
    View Blog function that returns the BLog page and data
    """
    subscribers = Subscriber.query.all()
    blog_form = BlogForm()
    blog = Blog.query.order_by(Blog.date.desc()).all()
    if blog_form.validate_on_submit():
        title_blog= blog_form.title_blog.data
        description = blog_form.description.data
        new_blog = Blog(title_blog=title_blog, description=description, user=current_user)
        db.session.add(new_blog)
        db.session.commit()
        for subscriber in subscribers:
            mail_message("Alert New Blog","email/new_blog",subscriber.email,new_blog=new_blog)
        return redirect(url_for('main.index'))
        flash('New Blog Posted')
        return redirect(url_for('main.theblog'))
    title = 'My Blog'
    return render_template('comment.html', title=title, blog_form=blog_form)

@main.route('/Update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_blog(id):
    blog = Blog.query.get_or_404(id)
    if blog.user != current_user:
        abort(403)
    form = BlogForm()
    if form.validate_on_submit():
        blog.title_blog = form.title_blog.data
        blog.description = form.description.data
        db.session.commit()

        return redirect(url_for('main.theblog'))
    elif request.method == 'GET':
        form.title_blog.data = blog.title_blog
        form.description.data = blog.description
    return render_template('edit_comment.html', form=form)



@main.route('/blog/allblogs', methods=['GET', 'POST'])
@login_required
def theblog():
    blogs = Blog.query.all()
    return render_template('mycomments.html', blogs=blogs)


@main.route('/view/<int:id>', methods=['GET', 'POST'])
@login_required
def view(id):
    blog = Blog.query.get_or_404(id)
    blog_comments = Comment.query.filter_by(blog_id=id).all()
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        new_comment = Comment(blog_id=id, comment=comment_form.comment.data, user=current_user)
        new_comment.save_comment()
    return render_template('view.html', blog=blog, blog_comments=blog_comments, comment_form=comment_form)


@main.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    blog = Blog.query.get_or_404(id)
    if blog.user != current_user:
        abort(403)
    db.session.delete(blog)
    db.session.commit()
 
    return redirect(url_for('main.theblog'))

@main.route('/delete_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def delete_comment(comment_id):
    comment =Comment.query.get_or_404(comment_id)
    if (comment.user.id) != current_user.id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('comment succesfully deleted')
    return redirect (url_for('main.theblog'))

@main.route('/subscribe', methods=['GET','POST'])
def subscriber():
    blogQuote = get_blogQuotes()
    subscriber_form=SubscriberForm()
    blog = Blog.query.order_by(Blog.date.desc()).all()

    if subscriber_form.validate_on_submit():

        subscriber= Subscriber(email=subscriber_form.email.data,name = subscriber_form.name.data)

        db.session.add(subscriber)
        db.session.commit()

        mail_message("Welcome to credentials","email/subscriber",subscriber.email,subscriber=subscriber)

        title= "Credentials"
        return render_template('index.html',title=title, blog=blog, blogQuote=blogQuote)

    subscriber = Blog.query.all()

    blog = Blog.query.all()


    return render_template('subscribe.html',subscriber=subscriber,subscriber_form=subscriber_form,blog=blog)


@main.route('/article/<uname>/new',methods= ['GET','POST'])
@login_required
def new_article(uname):
    if request.method=='POST':
        article_title=request.form['title']
        article_body=request.form['body']
        article_tag=request.form['tag']
        filename = photos.save(request.files['photo'])
        article_cover_path=f'photos/{filename}'
        
        new_article=Article(article_title=article_title,article_body=article_body,article_tag=article_tag,article_cover_path=article_cover_path,user_id=current_user.id)
        new_article.save_article()

        flash('Article added')
        return redirect(url_for('main.profile',uname=uname))

    return render_template('new_article.html') 

@main.route('/articles/tag/<tag>')
@login_required
def article_by_tag(tag):

    '''
    View root page function that returns pitch category page with pitches from category selected
    '''
    articles=Article.query.filter_by(article_tag=tag).order_by(Article.posted.desc()).all()
    
    return render_template('article_by_tag.html',articles=articles,tag=tag)  

@main.route('/article_details/<article_id>', methods = ['GET','POST'])
@login_required
def article_details(article_id):

    '''
    View article details function that returns article_details and comment form
    '''

    form = CommentForm()
    article=Article.query.get(article_id)
    comments=Comment.query.filter_by(article_id=article_id).order_by(Comment.posted.desc()).all()
    
    if form.validate_on_submit():
        comment = form.comment.data
        
        # Updated comment instance
        new_comment = Comment(comment=comment,user=current_user,article=article)

        # save review method
        new_comment.save_comment()
        article.article_comments_count = article.article_comments_count+1

        db.session.add(article)
        db.session.commit()
        flash('Comment posted')
        return redirect(url_for('main.article_details',article_id=article_id))

    return render_template('article_details.html',comment_form=form,article=article,comments=comments) 


@main.route('/article_upvote/<article_id>')
@login_required
def article_upvote(article_id):
    '''
    View function to add do upvote on article like btn click
    '''
    article=Article.query.get(article_id)
    article.article_upvotes=article.article_upvotes+1
    db.session.add(article)
    db.session.commit() 
    flash('You liked this article') 
    return redirect(url_for('main.article_details',article_id=article_id)) 


@main.route('/article_downvote/<article_id>')
@login_required
def article_downvote(article_id):
    '''
    View function to add downvote on article dislike btn click
    '''
    article=Article.query.get(article_id)
    article.article_downvotes=article.article_downvotes+1
    db.session.add(article)
    db.session.commit()  
    flash('You disliked this article')
    return redirect(url_for('main.article_details',article_id=article_id))   


# @main.route('/comment/delete/<comment_id>/<article_id>')
# @login_required
# def delete_comment(comment_id,article_id):
#     comment = Comment.query.get(comment_id)
#     db.session.delete(comment)
#     article=Article.query.get(article_id)
#     article.article_comments_count = article.article_comments_count-1
#     db.session.add(article)
#     db.session.commit()
#     flash('You deleted a comment')
#     return redirect(url_for('main.article_details',article_id=article_id))  


# @main.route('/article/delete/<article_id>')
# @login_required
# def delete_article(article_id):
#   article = Article.query.get(article_id)
#   db.session.delete(article)
#   db.session.commit()
#   flash('You deleted an article')
#   return redirect(url_for('main.index'))
 

