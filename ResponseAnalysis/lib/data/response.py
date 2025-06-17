from pydantic import BaseModel, Field
import hashlib

class Response(BaseModel):
    """
    Represents the ground truth response (expected) from an AI agent
    for a given prompt.
    Attributes:
        response_text (str): The ground truth expected response.
        response_type (str): Type of response (e.g., 'GT', 'GTDesc', etc.).
        kwargs (dict): Additional keyword arguments for future extensibility.
    """
    response_text: str = Field(..., description="The text of the response.")
    response_type: str = Field(..., description="The type of the response, e.g., 'GT', 'GTDesc', etc.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")

    def __init__(self, response_text: str, response_type: str, **kwargs):
        """
        Initializes a Response instance.

        Args:
            response_text (str): The text of the response.
            response_type (str): The type of the response, e.g., 'GT', 'GTDesc', etc.   
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(response_text=response_text, 
                         response_type=response_type,
                         kwargs=kwargs)

    def __str__(self):
        """Returns a string representation of the response."""
        return f"Response Text: {self.response_text}\nResponse Type: {self.response_type}"
    
    def __repr__(self): 
        """Returns a string representation of the Response instance for debugging."""
        return (f"Response(response_text={self.response_text!r}, "
                f"response_type={self.response_type!r})")
    
    def __eq__(self, other):
        """
        Checks equality between two Response instances.
        Compares both expected and predicted responses.
        """
        if not isinstance(other, Response):
            return False
        return (self.response_text == other.response_text and
                self.response_type == other.response_type)
    
    def __hash__(self):
        """
        Returns a hash of the Response instance.
        Uses the hash of both expected and predicted responses.
        """
        return hash((self.response_text, self.response_type))
    
    @property
    def digest(self):
        """
        Returns a digest of the response.
        This can be used for quick comparisons or checks.
        """
        # compute the hash value for the prompt
        hashing = hashlib.sha1()
        hashing.update(str(self).encode('utf-8'))
        return hashing.hexdigest()
        
    