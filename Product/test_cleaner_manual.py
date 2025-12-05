from  Product.cleaner import clean_company_and_ticker

# Each entry: (user_input, expected_company, expected_ticker)
TEST_CASES = [
    ("Richtech", "Richtech Robotics", "RR"),
    ("Richtech robotics", "Richtech Robotics", "RR"),

    ("ASML", "ASML Holding N.V.", "ASML"),
    ("ASML Holding N.V.", "ASML Holding N.V.", "ASML"),

    ("BTCFX", "Bitcoin ProFund Investor", "BTCFX"),
    ("Bitcoin ProFund Investor", "Bitcoin ProFund Investor", "BTCFX"),

    ("Micropolis", "Micropolis Holdings", "MCRP"),
    ("Micropolis Holdings", "Micropolis Holdings", "MCRP"),

    ("Gold", "Gold", "GC=F"),

    ("CG", "The Carlyle Group Inc.", "CG"),
    ("The Carlyle Group Inc.", "The Carlyle Group Inc.", "CG"),

    ("UPRO", "ProShares UltraPro S&P 500", "UPRO"),
    ("triple leveraged s and p etf", "ProShares UltraPro S&P 500", "UPRO"),
]


def pretty_ok(got: str, want: str) -> bool:
    g = " ".join(got.lower().split())
    w = " ".join(want.lower().split())
    return (w in g) or (g in w)


if __name__ == "__main__":
    for user_input, want_company, want_ticker in TEST_CASES:
        got = clean_company_and_ticker(user_input)

        got_company = got["company"]
        got_ticker  = got["ticker"]

        company_ok = pretty_ok(got_company, want_company)
        ticker_ok  = (got_ticker == want_ticker)

        print("INPUT:", user_input)
        print("  got:", got)
        print("  expect:", {"company": want_company, "ticker": want_ticker})
        print(f"  company_match: {company_ok} | ticker_match: {ticker_ok}")
        print("-" * 60)
