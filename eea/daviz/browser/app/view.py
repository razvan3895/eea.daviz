""" Module that contains default view
"""
import logging
import json as simplejson
from zope.component import queryAdapter, queryMultiAdapter
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from eea.daviz.interfaces import IDavizConfig

logger = logging.getLogger('eea.daviz.browser')

class JSONView(BrowserView):
    """ Abstract view to provide "daviz-view.json" multiadapter
    """
    def json(self):
        """ Implement this method in order to provide a valid exhibit JSON
        """
        res = {'items': [], 'properties': {}}
        return simplejson.dumps(res)


class View(JSONView):
    """ daviz-view.json for IExhibitJson objects
    """
    def __init__(self, context, request):
        super(View, self).__init__(context, request)
        self.accessor = queryAdapter(self.context, IDavizConfig)

    def json(self):
        """ Returns json dump of result
        """
        res = self.accessor.json
        return simplejson.dumps(dict(res))

    @property
    def facets(self):
        """ Returns facets
        """
        facets = self.accessor.facets
        for facet in facets:
            if not facet.get('show', False):
                continue
            yield facet.get('name')

    @property
    def views(self):
        """ Returns views
        """
        views = self.accessor.views
        for view in views:
            yield view.get('name')

    @property
    def sources(self):
        """ External sources
        """
        sources = self.accessor.sources
        for source in sources:
            yield source

    @property
    def gmapkey(self):
        """ Get Google Maps key from
            portal_properties.geographical_properties.google_key
        """
        ptool = getToolByName(self.context, 'portal_properties')
        props = getattr(ptool, 'geographical_properties', '')
        return getattr(props, 'google_key', '')

    def get_facet(self, name):
        """ Get faceted by name
        """
        facet = self.accessor.facet(key=name)
        facet_type = facet.get('type')
        if not isinstance(facet_type, unicode):
            facet_type = facet_type.decode('utf-8')
        view = queryMultiAdapter((self.context, self.request), name=facet_type)
        view.data = facet
        return view

    def get_view(self, name):
        """ Get view by name
        """
        if not isinstance(name, unicode):
            name = name.decode('utf-8')
        view = queryMultiAdapter((self.context, self.request), name=name)
        return view

class RelatedItemsJSON(JSONView):
    """ Merged JSON from related items
    """
    def json(self):
        """ JSON
        """
        relatedItems = self.context.getRelatedItems()

        new_json = {'items': [], 'properties': {}}
        for item in relatedItems:
            daviz_json = queryMultiAdapter(
                (item, self.request), name=u'daviz-view.json')

            if not daviz_json:
                continue

            try:
                daviz_json = simplejson.loads(daviz_json())
            except Exception, err:
                logger.debug(err)
                continue

            new_json['items'].extend(daviz_json.get('items', []))
            new_json['properties'].update(daviz_json.get('properties', {}))

        return simplejson.dumps(new_json)
