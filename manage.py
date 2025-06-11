from flask import Flask
from app import app, db  # 导入你的 app 实例
from flask_migrate import Migrate
from models import User, Customisation, Connection, Message

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()

# 注册 CLI 命令
from flask.cli import FlaskGroup
cli = FlaskGroup(app)

if __name__ == '__main__':
    cli()
