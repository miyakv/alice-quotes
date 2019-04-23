base_url = "https://ru.wikiquote.org/w/api.php"
quote_of_the_day_url = "https://ru.wikiquote.org/wiki/%D0%92%D0%B8%D0%BA%D0%B8%D1%86%D0%B8%D1%82%D0%B0%D1%82%D0%BD%D0%B8%D0%BA:%D0%98%D0%B7%D0%B1%D1%80%D0%B0%D0%BD%D0%BD%D0%B0%D1%8F_%D1%86%D0%B8%D1%82%D0%B0%D1%82%D0%B0"


def quote_of_the_day_parser(html):
    quote_and_author = html.table("td")[2]("td")

    quote = quote_and_author[0].text.strip()
    author = quote_and_author[1].text.replace("~", "").strip()

    return quote, author


non_quote_sections = ['См. также']
