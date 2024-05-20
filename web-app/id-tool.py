from flask import Flask, render_template, request
from ibdgc_db.cli import cli
import click

app = Flask(__name__)

@app.route('/')
def index():
    centers = utils.get_centers()
    return render_template('index.html') 

@app.route('/lookup', methods=['POST'])
def lookup():
    index = request.form['index']
    center = request.form['center']
    value = request.form['value']
    
    ctx = click.Context(cli, info_name=cli.name)
    args = ['--index', index, '--center', center, value]
    
    try:
        result = cli.invoke(ctx, ['lookup'] + args)
        return result.output
    
    except click.ClickException as e:
        return str(e), 400

if __name__ == '__main__':
    app.run()
