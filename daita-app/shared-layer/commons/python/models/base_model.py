

from decimal import Decimal


class BaseModel():
    def __init__(self) -> None:
        pass

    def convert_decimal_indb_item(self, item):
        if item:
            for key, value in item.items():
                if type(value) is Decimal:
                    item[key] = int(value)
        
        return item

    def put_item_w_condition(self, item, condition):
        self.table.put_item(
                    Item = item,
                    ConditionExpression = condition
                )
        return

    def batch_write(self, ls_item_request):
        try:
            with self.table.batch_writer() as batch:
                for item in ls_item_request:
                    batch.put_item(Item=item)
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))