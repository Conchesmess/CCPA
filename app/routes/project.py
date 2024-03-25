# These routes are an example of how to use data, forms and routes to create
# a blog where a blogs and comments on those blogs can be
# Created, Read, Updated or Deleted (CRUD)

from app import app
import mongoengine.errors
from flask import render_template, flash, redirect, url_for
from flask_login import current_user
from app.classes.data import require_role, Project, Milestone, ProjPost
from app.classes.forms import ProjectForm, MilestoneForm, ProjPostForm
from flask_login import login_required
import datetime as dt

@app.route('/project/post/new/<pid>/<mid>', methods=['GET','POST'])
@login_required
def projectPostNew(pid=None,mid=None):
    form = ProjPostForm()

    if pid:
        try:
            project = Project.objects.get(pk = pid)
        except:
            flash('That project does not exist.')
            return redirect(url_for('projectMy'))
        else:
            try:
                milestone = project.milestones.get(oid = mid)
            except:
                flash("That Milestone doesn't exist")
                return redirect(url_for('projectMy'))

    else:
        try:
            project = Project.objects.get(owner = current_user,status='In Progress')
        except:
            flash("You do not have any projects that are 'In Progress'")
            return redirect(url_for('projectMy'))

    if milestone:
        form.milestone.choices = [(milestone.oid,milestone.name)]
    else:
        milestoneChoices = []

        for milestone in project.milestones:
            milestoneChoices.append((milestone.oid,milestone.name))

        form.milestone.choices = milestoneChoices
        

    fail = 0

    if form.validate_on_submit():
        now = dt.datetime.utcnow()
        nowdate=now.replace(hour=0, minute=0).strftime('%Y-%m-%d %H:%M')
        try:
            posts = ProjPost.objects.get(project=project,post_type=form.post_type.data,createDateTime__gt = nowdate)
        except mongoengine.errors.MultipleObjectsReturned:
            flash(f'You have more than one post for this day, this project and {form.post_type.data}. This should not happen. Please delete one' )
        except mongoengine.errors.DoesNotExist:
            pass
        else:
            flash(f"You already have a post for this day, this project and {form.post_type.data}. Delete or edit that post.")
            return redirect(url_for('projectMy'))

        if form.post_type.data.lower() == "reflection":
            print("intention check if reflection")
            try:
                post = ProjPost.objects.get(project=project,post_type__iexact='intention',createDateTime__gt = nowdate)
            except mongoengine.errors.DoesNotExist:
                flash("You can't post a reflection if you haven't posted today's intention.")
                return redirect(url_for('projectMy'))

        if form.post_type.data.lower() == "intention":
            if int(form.confidence.data) == 0:
                form.confidence.errors.append("Confidence is required if your post type is Intention.")
                fail=1
            if len(form.intention.data) == 0:
                form.intention.errors.append("Intention is required if your post type is Intention.")
                fail=1
        elif form.post_type.data.lower() == "reflection":
            if int(form.satisfaction.data) == 0:
                form.satisfaction.errors.append("Satisfaction is required if your post type is Reflection.")
                fail=1
            if len(form.reflection.data) == 0:
                form.reflection.errors.append("Reflection is required if your post type is Reflection.")
                fail=1
        if fail == 1:
            return render_template("projects/project_post_form.html", form=form, project=project)

        newPost = ProjPost(
            post_type = form.post_type.data,
            confidence = form.confidence.data,
            intention = form.intention.data,
            satisfaction = form.satisfaction.data,
            reflection = form.reflection.data,
            owner = current_user,
            project = project,
            milestoneOID = form.milestone.data,
            image_reflection_src = form.image_reflection_src.data
        )

        # if form.image_reflection.data:
        #     # if newPost.image_reflection:
        #     #     newPost.image_reflection.delete()
        #     newPost.image_reflection.put(form.image_reflection.data, content_type = 'image/jpeg')

        newPost.save()

        return redirect(url_for("projectMy"))

    return render_template("projects/project_post_form.html", form=form, project=project)

@app.route('/project/post/delete/<postID>')
@login_required
def projectPostDelete(postID):
    try:
        delPost = ProjPost.objects.get(pk=postID)
    except:
        flash("That post doesn't exist.")
        return redirect(url_for('projectMy'))
    project = delPost.project
    delPost.delete()
    flash("Post deleted")
    return redirect(url_for('project',pid=project.id))


@app.route('/project/definition')
def projectDef():
    return render_template('projects/project_def.html')

@app.route('/project/list')
@login_required
def projectList():
    projects = Project.objects()
    return render_template('projects/project_list.html',projects=projects)

@app.route('/project/delete/<pid>')
@login_required
def projectDelete(pid):
    try:
        projDel = Project.objects.get(pk=pid)
    except mongoengine.errors.DoesNotExist:
        flash("That project doesn't exist")
        return render_template('index.html')

    if projDel.owner != current_user and not session['isadmin']:
        flash("You can't delete that project." )
        return render_template('index.html')
    
    if len(projDel.milestones) > 0:
        flash("You can't delete a project that has Milestones.")
        return redirect(url_for('project',pid=projDel.id))

    projDel.delete()
    flash('Project has been deleted')

    return redirect(url_for('projectList'))    

@app.route('/project/my')
@login_required
def projectMy():
    try:
        proj = Project.objects.get(owner=current_user,status='In Progress')
    except mongoengine.errors.DoesNotExist:
        flash("You don't have a project that is set to 'In Progress'. You should make one!")
        return render_template('index.html')
    except mongoengine.errors.MultipleObjectsReturned:
        flash("Hmmm, you have more than one project that is 'In Progress'.  That should not happen.")
        return redirect(url_for('projectList'))
    else:
        return redirect(url_for('project',pid=proj.id))

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def projectNew():
    form = ProjectForm()

    try:
        projMy = Project.objects.get(owner=current_user, status = "In Progress")
    except mongoengine.errors.DoesNotExist:
        pass
    else:
        flash('You have an active project.')
        return redirect(url_for('projectMy'))

    if form.validate_on_submit():

        newProj = Project(
            owner = current_user,
            name = form.name.data,
            status = "In Progress",
            product = form.product.data,
            createDateTime = dt.datetime.utcnow()
        )

        newProj.save()

        return redirect(url_for('project',pid=newProj.id))
    
    return render_template('projects/project_form.html', form=form)

@app.route('/project/edit/<pid>', methods=['GET', 'POST'])
@login_required
def projectEdit(pid):
    form = ProjectForm()
    try:
        projEdit = Project.objects.get(pk=pid)
    except mongoengine.errors.DoesNotExist:
        flash('That projject does not exist')
        return render_template('index.html')

    if form.validate_on_submit():

        projEdit.update(
            owner = current_user,
            name = form.name.data,
            status = form.status.data,
            #desc = form.desc.data,
            product = form.product.data,
            createDateTime = dt.datetime.utcnow()
        )

        return redirect(url_for('project',pid=pid))
    
    form.name.data = projEdit.name
    form.status.data = projEdit.status
    #form.desc.data = projEdit.desc
    form.product.process_data(projEdit.product)
    
    return render_template('projects/project_form.html', form=form)

@app.route('/project/<pid>', methods=['POST','GET'])
@login_required
def project(pid):

    form = MilestoneForm()

    try:
        proj = Project.objects.get(pk=pid)
    except mongoengine.errors.DoesNotExist:
        flash("That project doesn't exist")
        return redirect(url_for('project', pid=pid))
    
    if form.validate_on_submit():
        if len(proj.milestones) == 0 or proj.milestones[-1].status == "Done":
            num = len(proj.milestones)+1
            proj.milestones.create(
                number = num,
                name = form.name.data,
                desc = form.desc.data,
                status = "In Progress"
            )
            
            proj.save()

        else:
            flash("You can't create a new milestone until the previous one is marked done.")
    
    posts = ProjPost.objects(project = proj)
    for ms in proj.milestones:
        ms.posts = []
        for post in posts:
            if post.milestoneOID == str(ms.oid):
                ms.posts.append(post)


        
    return render_template('projects/project.html', proj=proj, form=form)

@app.route('/project/milestone/delete/<pid>/<mid>')
@login_required
def projectMsDel(pid,mid):

    proj = Project.objects.get(pk=pid)
    if proj.owner == current_user or session['isadmin']:
        if proj.milestones[-1].status == 'Delete':
            proj.milestones.filter(oid=mid).delete()
            proj.save()
        else:
            flash('you can only delete a milestone that has status marked as "Delete".')
    else:
        flash("You can't delete that milestone because you don't own.")
    
    return redirect(url_for('project',pid=pid))

@app.route('/project/milestone/edit/<pid>/<mid>', methods=['GET','POST'])
@login_required
def projectMsEdit(pid,mid):

    form = MilestoneForm()

    proj = Project.objects.get(pk=pid)

    ms = proj.milestones.get(oid=mid)

    if form.validate_on_submit():
        proj.milestones.filter(oid=mid).update(
            name = form.name.data,
            desc = form.desc.data,
            status = form.status.data
        )
        proj.save()

        return redirect(url_for('project', pid=pid))
    
    form.name.process_data(ms.name)
    form.desc.process_data(ms.desc)
    form.status.process_data(ms.status)

    return render_template('projects/project.html',proj=proj,form=form,edit=True)

@app.route('/project/milestone/new/<pid>', methods=['GET','POST'])
@login_required
def projectMsNew(pid):

    form = MilestoneForm()

    proj = Project.objects.get(pk=pid)

    if form.validate_on_submit():
        proj.milestones.create(
            name = form.name.data,
            desc = form.desc.data,
            status = form.status.data
        )
        proj.save()

        return redirect(url_for('project', pid=pid))

    return render_template('projects/project.html',proj=proj,form=form,edit=True)

