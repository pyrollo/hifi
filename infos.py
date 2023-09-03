
class DatabaseInformation:
    def __init__(self, file, size, count):
        self.file = file
        self.size = size
        self.count = count

    def __str__(self):
        return "%s: %d files (%d bytes) indexed." % (self.file, self.count, self.size)

class PathInformation:
    def __init__(self, path, size, count):
        self.path = path
        self.size = size
        self.count = count

    def __str__(self):
        return "%s: %d files (%d bytes) indexed." % (self.path, self.count, self.size)
