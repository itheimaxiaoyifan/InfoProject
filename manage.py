from Info import create_app, db, models
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from Info.models import User

app = create_app('develop')
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.option("-n", dest="name")
@manager.option("-p", dest="password")
def createsuperuser(name, password):
    if not all([name, password]):
        print("参数不全")
        return

    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
        print("创建成功")
        return
    except Exception as e:
        print("创建失败： %s" % e)
        db.session.rollback()


if __name__ == '__main__':
    manager.run()
