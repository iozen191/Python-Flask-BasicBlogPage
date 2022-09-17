

from sqlite3 import Cursor
from unittest import result
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#-------------------------------------------------------------
# DECORATORLER
#-------------------------------------------------------------

#Kullanıcı Giriş Decarator'u
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntümelek İçin Giriş Yapmanız Gerekiyor...","danger")
            return redirect(url_for("login"))
    return decorated_function

#----------------------------------------------------------------
# CLASSLAR
#----------------------------------------------------------------

# Kullanıcı Kayıt Formu

class RegisterForm(Form):
    name = StringField("İsim Soyisim:",validators=[validators.Length(min=4,max=25, message="Lütfen 4-25 karakter arasında giriş yapınız...")])
    username = StringField("Kullanıcı Adı:",validators=[validators.Length(min=4,max=25,message="Lütfen 4-25 karakter arasında giriş yapınız...")])
    email = StringField("Email Adresi:",validators=[validators.Email(message="Lütfen Geçerli Bir Email Adresi Girin...")])
    password = PasswordField("Parola:",validators=[
        validators.Length(min=4,max=30,message="Lütfen 4-25 karakter arasında giriş yapınız..."),
        validators.DataRequired(message= "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor..."),
    ])
    confirm = PasswordField("Parolanızı Tekrar Giriniz:")

# Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı: ")
    password = PasswordField("Parola: ")

#Makele Formu
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.Length(min=5,max=100,message="Makale Başlığı 5 ile 100 Harf Arasında Değerden Oluşmalıdır...")])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10,message="Makale İçeriği En Az 10 Harften Oluşmalıdır...")])


#----------------------------------------------------------------
# MySQL Bağlantısı
#----------------------------------------------------------------
app =  Flask(__name__)
app.secret_key = "banzblog33"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "banzblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)
#--------------------------------------------------------------

# Sayfalara Bağlantı
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")



#----------------------------------------------------------------
# PANALLER
#----------------------------------------------------------------

#Kayıt Olma
@app.route("/register",methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        #Database Bağlantısı
        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))
    
    else:
        return render_template("register.html", form = form)


# Giriş İşlemi
@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username  = %s " 
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız...","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle Bir Kullanıcı Bulunmuyor...","danger")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)

# Çıkış İşlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")



# ---------------------------------------------------------------
# MAKALELER
#----------------------------------------------------------------


# Makale Ekleme
@app.route("/addarticle",methods = ["GET","POST"])
@login_required
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html", form = form)

#Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles"
    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

#Makale Id
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "DELETE FROM articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle Bir Makale Yok Veya Bu Makaleyi Silme Yetkiniz Yok...","danger")
        return redirect(url_for("index"))

#Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Böyle Bir Makale Yok Veya Bu İşleme Yetkiniz Yok...","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        #POST REQUETS
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "UPDATE articles SET title = %s ,content = %s WHERE id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale Başaryıla Güncellendi","success")
        return redirect(url_for("dashboard"))

#Makale Arama
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE title LIKE '%" + keyword + "%' "
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles=articles)









if __name__ == '__main__':
    app.run(debug=True)
