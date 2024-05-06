#import pkg_resources
#try:
#    __version__ = pkg_resources.get_distribution(__name__).version
#except pkg_resources.DistributionNotFound:
#    pass

class Software:
    def __init__(self):
        self.__file__ = "."

# ca06867143df4873726d8a756178615b39b9904c + https://github.com/lambdaconcept/lambdasoc/pull/19
__version__ = "vendored lambdasoc"
software = Software()
