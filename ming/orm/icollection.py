def instrument(obj, tracker):
    if isinstance(obj, dict):
        return InstrumentedObj(
            tracker,
            ((k, instrument(v, tracker)) for k,v in obj.iteritems()))
    elif isinstance(obj, list):
        return InstrumentedList(
            tracker,
            (instrument(v, tracker) for v in obj))
    else:
        return obj

class InstrumentedCollection(object):

    def __init__(self, tracker):
        self._tracker = tracker

class InstrumentedObj(InstrumentedCollection, dict):

    def __init__(self, tracker, *args, **kwargs):
        InstrumentedCollection.__init__(self, tracker)
        dict.__init__(self, *args, **kwargs)

    def __setitem__(self, name, value):
        old_value = self.get(name, ())
        dict.__setitem__(self, name, value)
        if old_value is not ():
            self._tracker.removed_item(old_value)
        self._tracker.added_item(value)

    def __delitem__(self, name):
        value = self[name]
        dict.__delitem__(self, name)
        self._tracker.removed_item(value)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError, name

    def clear(self):
        dict.clear(self)
        self._tracker.cleared()

    def pop(self, k, *args):
        result = dict.pop(self, k, *args)
        self._remoed_item(result)
        return result

    def popitem(self):
        k,v = dict.popitem(self)
        self._tracker.removed_item(v)
        return k,v

    def update(self, *args, **kwargs):
        'Must do all the work ourselves so we track the related objects'
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, dict): arg = arg.iteritems()
            for k,v in arg:
                if k in self: del self[k]
                self[k] = v
        for k,v in kwargs.iteritems():
            if k in self: del self[k]
            self[k] = v

class InstrumentedList(InstrumentedCollection, list):

    def __init__(self, tracker, *args, **kwargs):
        InstrumentedCollection.__init__(self, tracker)
        list.__init__(self, *args, **kwargs)

    def __setitem__(self, i, value):
        list.__setitem__(self, i, value)
        self._tracker.removed_item(self[i])
        self._tracker.added_item(value)

    def __setslice__(self, i, j, y):
        old_items = self[i:j]
        list.__setslice__(self, i, j, y)
        for item in old_items:
            self._tracker.removed_item(item)
        for item in self[i:j]:
            self._tracker.added_item(item)

    def __delitem__(self, i):
        item = self[i]
        list.__delitem__(self, i)
        self._tracker.removed_item(item)

    def __delslice__(self, i, j):
        for item in self[i:j]:
            self._tracker.removed_item(item)
        list.__delslice__(self, i, j)

    def __iadd__(self, y):
        for x in y:
            self.append(x)

    def __imul__(self, y):
        if y <= 0:
            self[:] = []
        else:
            orig = self[:]
            for i in range(1,y):
                self += orig

    def append(self, value):
        list.append(self, value)
        self._tracker.added_item(value)

    def extend(self, iterable):
        for item in iterable:
            self.append(item)

    def insert(self, index, value):
        list.insert(self, index, value)
        self._tracker.added_item(value)

    def pop(self, index=()):
        if index is not ():
            result = list.pop()
        else:
            result = list.pop(index)
        self._tracker.removed_item(result)
        return result
           
    def remove(self, value):
        try:
            index = self.index(value)
        except ValueError:
            raise ValueError, 'InstrumentedList.remove(x): x not in list'
        del self[index]
        
