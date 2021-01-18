class RoundFloat(float):
    """
    Float sub class to display two decimal places and
    rounding to nearest float
    """
    def __new__(cls, value=0, places=2):
        return float.__new__(cls, value)
    def __init__(self, value=0, places=2):
        self.places = str(places)
    def __repr__(self):
        return ("%." + self.places + "f") % self
    __str__ = __repr__

