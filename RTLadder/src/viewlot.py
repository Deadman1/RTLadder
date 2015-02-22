from main import BaseHandler, get_template

import lot


class ViewLotPage(BaseHandler):
    def get(self, lotID):
        container = lot.getLot(lotID)
        self.response.write(get_template('viewlot.html').render({'container': container, 'lotrendered': container.render() }))