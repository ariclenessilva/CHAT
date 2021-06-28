# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 09:53:02 2019

@author: Ariclenes Silva hugo 

"""
from flask import Flask, render_template, request, redirect, jsonify, url_for, session as session2, json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from threading import Lock
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect

Base = declarative_base()

async_mode = None

###################3 Object Relational of the database ########################################
class Groups(Base):
    __tablename__ = 'group'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False)
    room = Column(String(80), nullable=False)
    parent_id = Column(Integer, ForeignKey('user.id'))
    
class Messages(Base):
    __tablename__ = 'message'
    
    id = Column(Integer, primary_key=True)
    room = Column(String(80), nullable=False)
    messages = Column(String(1000), nullable=True)
    sender = Column(String(80), nullable=True)
    dates = Column(String(80), nullable=True)
    parent_id = Column(Integer, ForeignKey('user.id'))
    
class Contacts(Base):
    __tablename__ = 'contact'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False)
    room = Column(String(80), nullable=True)
    parent_id = Column(Integer, ForeignKey('user.id'))
    
class Users(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False)
    password = Column(String(250))
    children = relationship("Contacts", backref='user',
                                lazy='dynamic')
    children2 = relationship("Messages", backref='user',
                                lazy='dynamic')
    children3 = relationship("Groups", backref='user',
                                lazy='dynamic')

#####################################################################################
app = Flask(__name__)   
engine = create_engine('sqlite:///database/chat_db.db')
Base.metadata.create_all(engine)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

###################### Users section #######################################################################
@app.route('/', methods=['GET', 'POST'])
def login():
    session = DBSession()
    if 'username' in session2:
        user_check=session.query(Users).filter_by(username=session2['username']).first()
        
        num_all_messages=user_check.children2.count()
        
        return render_template('index.html', async_mode=socketio.async_mode, username=session2['username'], \
                               list_contact=user_check.children, all_messages=user_check.children2, \
                               num_all_messages=num_all_messages, list_groups=user_check.children3)
    else:
        if request.method == 'POST':
            if request.form['password']=='FACEBOOK':
                user_check=session.query(Users).filter_by(username=request.form['username']).first()
                
                if user_check and request.form['password']==user_check.password:
                    session2['username'] = request.form['username']
                else:
                    user1 = Users(username=request.form['username'],password='FACEBOOK')
                    session.add(user1)
                    session.commit()
                
                user_check=session.query(Users).filter_by(username=session2['username']).first()
        
                num_all_messages=user_check.children2.count()
                
                return render_template('index.html', async_mode=socketio.async_mode, username=session2['username'], \
                                       list_contact=user_check.children, all_messages=user_check.children2, \
                                       num_all_messages=num_all_messages, list_groups=user_check.children3)
            
               # return render_template('index.html', username=request.form['username'], login_logout="Logout")
                    
            
            user_check=session.query(Users).filter_by(username=request.form['username']).first()
            if user_check and request.form['password']==user_check.password:
                session2['username'] = request.form['username']
            else:
                return render_template('fail_login.html')
            
            user_check=session.query(Users).filter_by(username=session2['username']).first()
        
            num_all_messages=user_check.children2.count()
            
            return render_template('index.html', async_mode=socketio.async_mode, username=session2['username'], \
                                   list_contact=user_check.children, all_messages=user_check.children2, \
                                   num_all_messages=num_all_messages, list_groups=user_check.children3)
            
        #    return render_template('index.html', username=user_check.username, login_logout="Logout")
        
        return render_template('login_welcome.html', the_appID='')
    
@app.route('/signup_page', methods=['GET', 'POST'])
def siggnup():
    session = DBSession()
    if request.method == 'POST':
        un = str(request.form['post_users_username'])
        pd = str(request.form['post_users_password'])
        
        user_check=session.query(Users).filter_by(username=un).first()
        
        if user_check and pd==user_check.password:
            return render_template('fail_sign.html')
        else:
            user1 = Users(username=un,password=pd)
            session.add(user1)
            session.commit()
    
            return render_template('added_user.html')
    else:
        return render_template('signup_page.html')

@app.route('/add_new_contact', methods=['GET', 'POST'])
def add_contact():
    session = DBSession()
    if request.method == 'POST':
        un = str(request.form['post_users_username'])
        
        user_check=session.query(Users).filter_by(username=session2['username']).first() 
        user_check2=session.query(Users).filter_by(username=un).first() # new_contact

        if user_check2 and user_check.children.filter_by(username=un).count()!=1 and user_check.username!=user_check2.username:
            if user_check2.children.filter_by(username=user_check.username).count()==1:
                the_user=user_check2.children.filter_by(username=user_check.username).first()
                user_check.children.append(Contacts(username=un, room=the_user.room))
            else:
                user_check.children.append(Contacts(username=un, room=str(user_check.username)+str(user_check2.username)))
            session.add(user_check)
            session.commit()
    
            return redirect(url_for('login'))
        else:
            return render_template('error_add_contact.html')
           
    else:
        return render_template('add_contact.html')
    
@app.route('/add_new_group', methods=['GET', 'POST'])
def add_cgroup():
    session = DBSession()
    if request.method == 'POST':
        un = str(request.form['post_users_username'])
        
        user_check=session.query(Users).filter_by(username=session2['username']).first() 
        user_check2=session.query(Groups).filter_by(username=un).first() # new_group

        if user_check2 and user_check.children3.filter_by(username=un).count()!=1:
            user_check.children3.append(Groups(username=un, room=un))
            session.add(user_check)
            session.commit()
    
            return redirect(url_for('login'))
        else:
            return render_template('error_add_group.html')
           
    else:
        return render_template('add_group.html')
 
@app.route('/create_group', methods=['GET', 'POST'])
def create_the_group():
    session = DBSession()
    if request.method == 'POST':
        un = str(request.form['post_users_username'])
        
        user_check=session.query(Users).filter_by(username=session2['username']).first() 
        user_check2=session.query(Groups).filter_by(username=un).first() # new_contact

        if not user_check2:
            the_group = Groups(username=un, room=un)
            user_check.children3.append(Groups(username=un, room=un))
            session.add(user_check)
            session.add(the_group)
            session.commit()
    
            return redirect(url_for('login'))
        else:
            return render_template('error_add_contact.html')
           
    else:
        return render_template('create_group.html')
    
    
@app.route('/logout')
def logout():
    session2.pop('username', None)
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(error):
    return "page_not_found"

@app.errorhandler(500)
def page_overload(e):
    return str(e)

with app.test_request_context():
    print(url_for('login'))
    
def background_thread():
    """Example of how to send server generated events to clients."""
    #count = 0
    #while True:
     #   socketio.sleep(10)
      #  count += 1
       # socketio.emit('my_response',
        #              {'data': 'Server generated event', 'count': count},
         #             namespace='/test')
    pass

########## manipulation of the Socket IO ###########################################################
class MyNamespace(Namespace):
    def on_my_event(self, message):
        session2['receive_count'] = session2.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session2['receive_count']})

    def on_my_broadcast_event(self, message):
        session2['receive_count'] = session2.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session2['receive_count']},
             broadcast=True)

    def on_join(self, message):
        join_room(message['room'])
        session2['receive_count'] = session2.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session2['receive_count']})

    def on_leave(self, message):
        leave_room(message['room'])
        session2['receive_count'] = session2.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session2['receive_count']})

    def on_close_room(self, message):
        session2['receive_count'] = session2.get('receive_count', 0) + 1
        emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                             'count': session2['receive_count']},
             room=message['room'])
        close_room(message['room'])

    def on_my_room_event(self, message):
        session2['receive_count'] = session2.get('receive_count', 0) + 1

        session = DBSession()
        
        user_check=session.query(Users).filter_by(username=session2['username']).first() # current_user 
        user_check2=session.query(Users).filter_by(username=message['the_contact_now']).first() # second_user
        user_check3=session.query(Groups).filter_by(username=message['the_contact_now']).first() # group
        
        if user_check2:
            user_check.children2.append(Messages(dates=message['sender_m'],sender=message['sender_m'],messages=message['data'], \
                                                 room=message['room']))
            user_check2.children2.append(Messages(dates=message['sender_m'],sender=message['sender_m'],messages=message['data'], \
                                                  room=message['room']))
            session.add(user_check)
            session.add(user_check2)
            
        elif user_check3:
            user_check.children2.append(Messages(dates=message['sender_m'],sender=message['sender_m'],messages=message['data'], \
                                                 room=message['room']))
            session.add(user_check)
        
        session.commit()
        
        user_check=session.query(Users).filter_by(username=session2['username']).first()
        
        emit('my_response',
             {'room':message['room'],'sender':message['sender_m'],'data': message['data'], 'count': session2['receive_count']},
             room=message['room'])

    def on_disconnect_request(self):
        session2['receive_count'] = session2.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'Disconnected!', 'count': session2['receive_count']})
        disconnect()

    def on_my_ping(self):
        emit('my_pong')

    def on_connect(self):
        global thread
        with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(background_thread)
        emit('my_response', {'data': 'Connected', 'count': 0})

    def on_disconnect(self):
        print('Client disconnected', request.sid)

socketio.on_namespace(MyNamespace('/test'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
