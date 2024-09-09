from flask import Flask
from flaskr.service.common.dtos import PageNationDTO

INPUT_TYPE_TEXT = "text"
INPUT_TYPE_DATE = "date"
INPUT_TYPE_SELECT = "select"
INPUT_TYPE_NUMBER = "number"
INPUT_TYPE_DATETIME = "datetime"
INPUT_TYPE_TIME = "time"
INPUT_TYPE_CHECKBOX = "checkbox"

# query list info


class TableColumnItem:
    def __init__(
        self,
        column,
        lable,
        items=None,
        model=None,
        display="",
        index_id="",
        display_view=None,
    ):
        self.column = column  # database column name
        self.lable = lable  # table column lable name,display in page
        self.items = items
        self.model = model
        self.display = display
        self.index_id = index_id
        self.display_view = display_view

    def __json__(self):
        return {
            "name": self.column,
            "lable": self.lable,
        }


# query input info
class InputItem:
    def __init__(
        self, column, label, query_type, input_type, input_options=None, input_view=None
    ):
        self.column = column
        self.label = label
        self.query_type = query_type
        self.input_type = input_type

        options = None
        if input_options is not None:
            options = []
            for key in input_options.keys():
                options.append({"value": input_options.get(key), "label": key})
        self.input_options = options
        self.input_view = input_view

    def __json__(self):
        return {
            "column": self.column,
            "label": self.label,
            "query_type": self.query_type,
            "input_type": self.input_type,
            "input_options": self.input_options,
        }


views = {}


class ViewDef:
    def __init__(
        self,
        name: str,
        items: list[TableColumnItem],
        queryinput: list[InputItem],
        model,
    ):
        self.name = name
        self.items = items
        self.model = model
        self.queryinput = queryinput
        views[name] = self

    def query(self, app: Flask, page: int = 1, page_size: int = 20, query=None):
        with app.app_context():
            app.logger.info(
                "query:"
                + str(query)
                + " page:"
                + str(page)
                + " page_size:"
                + str(page_size)
            )
            db_query = self.model.query
            if query:
                for key in query.keys():
                    input = next(filter(lambda x: x.column == key, self.queryinput))
                    if input.query_type == "like":
                        db_query = db_query.filter(
                            getattr(self.model, key).like(
                                "%" + str(query.get(key)) + "%"
                            )
                        )
                    else:
                        db_query = db_query.filter(
                            getattr(self.model, key) == query.get(key)
                        )
            count = db_query.count()
            if count == 0:
                return {}
            datas = (
                db_query.order_by(self.model.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            items = [
                {
                    "id": data.id,
                    **{
                        item.column: item.items.get(getattr(data, item.column), "")
                        if item.items
                        else str(getattr(data, item.column))
                        for item in self.items
                    },
                }
                for data in datas
            ]

            items_model = {}
            for item in items:
                for column in self.items:
                    if column.model and column.display:
                        if not items_model.get(column.model):
                            items_model[column.model] = []
                        items_model[column.model].append(item[column.column])
            for model in items_model.keys():
                app.logger.info("query")
                model_data = model.query.filter(
                    getattr(model, "user_id").in_(items_model[model])
                ).all()
                app.logger.info("model_data:" + str(model_data))
                for data in model_data:
                    for item in items:
                        pass

            app.logger.info("query done" + str(items))
            return PageNationDTO(page, page_size, count, items)

    def query_by_id(self, app: Flask, id):
        with app.app_context():
            app.logger.info("query_by_id:" + str(id))
            data = self.model.query.filter_by(id=id).first()
            if data is None:
                return {}
            item = {
                "id": data.id,
                "data": {
                    item.lable: str(getattr(data, item.column)) for item in self.items
                },
            }
            return item

    def query_by_id_and_property(self, app: Flask, id, property):
        with app.app_context():
            app.logger.info("query_by_id:" + str(id))
            data = self.model.query.filter_by(id=id).first()
            property_value = getattr(data, property)
            if property_value is None:
                return {}
            return data

    def get_view_def(self):
        return {"name": self.name, "items": self.items, "queryinput": self.queryinput}
