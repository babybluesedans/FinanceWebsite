import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    if db.execute(f"select * from stocks where user_id = ?;", session["user_id"]):
        stocks = db.execute(
            f"select * from stocks where user_id = ?;", session["user_id"]
        )
        for stock in stocks:
            newPrice = lookup(stock["stock"])
            shares = db.execute(
                "select shares from stocks where user_id = ? and stock = ?;",
                session["user_id"],
                stock["stock"],
            )
            shares = shares[0]["shares"]
            newPrice = float(newPrice["price"]) * float(shares)
            db.execute(
                f"update stocks set current_price = ? where user_id = ? and stock = ?;",
                newPrice,
                session["user_id"],
                stock["stock"],
            )
            allShares = db.execute(
                f"select current_price from stocks where user_id = ?;",
                session["user_id"],
            )
            totalInvested = 0.00
        for shares in allShares:
            totalInvested += float(shares["current_price"])
        cash = db.execute(f"select cash from users where id = ?;", session["user_id"])
        portfolioTotal = usd(cash[0]["cash"] + totalInvested)

        totalInvested = usd(totalInvested)
        for stock in stocks:
            stock["current_price"] = usd(stock["current_price"])
            stock["price_at_buy"] = usd(stock["price_at_buy"])
            stock["price_per_share"] = usd(stock["price_per_share"])
        cash = usd(cash[0]["cash"])

        return render_template(
            "index.html",
            stocks=stocks,
            totalInvested=totalInvested,
            cash=cash,
            portfolioTotal=portfolioTotal,
        )
    else:
        cash = db.execute(f"select cash from users where id = ?;", session["user_id"])
        cash = usd(cash[0]["cash"])
        portfolioTotal = cash
        return render_template("index.html", cash=cash, portfolioTotal=portfolioTotal)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        if (
            not shares.isnumeric()
            or float(shares) < 0
            or not float(shares).is_integer()
        ):
            return apology("invalid share entry")
        shares = float(shares)
        stats = lookup(symbol)
        if stats == None:
            return apology("stock not found")
        if shares <= 0:
            return apology("Must be > than 0")
        cash = db.execute(f"select cash from users where id = ?", session["user_id"])
        cash = cash[0]["cash"]
        price = stats["price"] * shares
        current_price = stats["price"]
        currentlyOwned = db.execute(
            f"select stock from stocks where user_id = ?", session["user_id"]
        )
        inStocks = False
        for stock in currentlyOwned:
            if stock["stock"] == symbol:
                inStocks = True
                currentShares = db.execute(
                    f"select shares from stocks where stock = ? and user_id = ?;",
                    symbol,
                    session["user_id"],
                )
                currentShares = float(currentShares[0]["shares"])

        if stats == None:
            return apology("stock not found")
        else:
            if price > cash:
                return apology("not enough money")
            else:
                if inStocks:
                    db.execute(
                        f"update stocks set shares = ? where stock = ? and user_id = ?;",
                        currentShares + shares,
                        symbol,
                        session["user_id"],
                    )
                else:
                    db.execute(
                        f"insert into stocks(user_id, stock, shares) values(?, ?, ?);",
                        session["user_id"],
                        symbol,
                        shares,
                    )
                db.execute(
                    f"update stocks set price_per_share = ? where stock = ? and user_id = ?;",
                    stats["price"],
                    symbol,
                    session["user_id"],
                )
                db.execute(
                    f"update stocks set price_at_buy = ?, current_price = ? where stock = ? and user_id = ?;",
                    current_price,
                    price,
                    symbol,
                    session["user_id"],
                )
                db.execute(
                    f"update users set cash = ? where id = ?;",
                    cash - price,
                    session["user_id"],
                )
                db.execute(
                    f"insert into transactions(user_id, stock, shares, amount) values(?, ?, ?, ?);",
                    session["user_id"],
                    symbol,
                    shares,
                    price,
                )

                return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        f"select * from transactions where user_id = ? order by timestamp desc;",
        session["user_id"],
    )
    for transaction in transactions:
        transaction["amount"] = usd(transaction["amount"])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        symbol = request.form.get("symbol")
        if not symbol.isalpha():
            return apology("invalid stock")
        stock = lookup(symbol)
        if stock == None:
            return apology("stock not found")
        price = usd(stock["price"])
        return render_template("quoted.html", stock=stock, price=price)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
        if (len(user) < 1) or (len(password) < 1):
            return apology("fill out form")
        password = generate_password_hash(password)
        confirmation = request.form.get("confirmation")
        if not (check_password_hash(password, confirmation)):
            return apology("Passwords dont match")
        try:
            db.execute(
                f"insert into users(username, hash) values('{user}', '{password}');"
            )
        except ValueError:
            return apology("username not unique")
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        if not (
            db.execute("select * from stocks where user_id = ?;", session["user_id"])
        ):
            return apology("no stocks to sell")
        stock = request.form.get("symbol")
        shares = request.form.get("shares")
        if not (stock or shares):
            return apology("form not filled out")

        current_shares = db.execute(
            f"select shares from stocks where user_id = ? and stock = ?;",
            session["user_id"],
            stock,
        )
        current_shares = current_shares[0]["shares"]
        cash = db.execute(f"select cash from users where id = ?;", session["user_id"])
        cash = cash[0]["cash"]
        current_price = db.execute(
            f"select price_per_share from stocks where stock = ? and user_id = ?;",
            stock,
            session["user_id"],
        )
        current_price = current_price[0]["price_per_share"]
        cash = float(cash) + (float(current_price) * float(shares))
        if float(shares) == float(current_shares):
            db.execute(
                f"delete from stocks where user_id = ? and stock = ?;",
                session["user_id"],
                stock,
            )
        elif float(shares) > float(current_shares):
            return apology("Not enough shares")
        else:
            new_shares = float(current_shares) - float(shares)
            db.execute(
                f"update stocks set shares = ? where user_id = ? and stock = ?;",
                new_shares,
                session["user_id"],
                stock,
            )

        db.execute(f"update users set cash = ? where id = ?;", cash, session["user_id"])
        db.execute(
            f"insert into transactions(user_id, stock, shares, amount) values(?, ?, -?, ?);",
            session["user_id"],
            stock,
            shares,
            (float(current_price) * float(shares)),
        )
        return redirect("/")
    else:
        stocks = db.execute(
            f"select stock from stocks where user_id = ?;", session["user_id"]
        )
        return render_template("sell.html", stocks=stocks)
