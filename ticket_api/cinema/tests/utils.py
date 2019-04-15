from hamcrest import all_of
from hamcrest import has_entries
from hamcrest import has_item
from hamcrest import not_


def is_page_of(*items, count):
    conditions = [has_item(item) for item in items]
    neg_conditions = [not_(has_item(item)) for item in items]
    conditions.append(not_(has_item(all_of(neg_conditions))))
    return has_entries(
        count=count,
        results=all_of(*conditions),
    )
