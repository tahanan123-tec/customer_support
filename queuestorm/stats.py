import threading
from collections import defaultdict, deque

class Stats:
    """
    A thread-safe singleton class to track system execution statistics,
    specifically tracking ticket volumes, case types, severities, human review requirements,
    and a log of the most recent classification results.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Implements the Singleton pattern using thread-safe locks.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Stats, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """
        Initializes counters and the recent request queue.
        Ensures initialization logic runs only once.
        """
        if getattr(self, "_initialized", False):
            return
        
        self.total: int = 0
        self.by_case_type: defaultdict = defaultdict(int)
        self.by_severity: defaultdict = defaultdict(int)
        self.human_review_count: int = 0
        self.recent: deque = deque(maxlen=50)
        self._lock = threading.Lock()
        self._initialized: bool = True

    def record(self, response: dict, timestamp: str) -> None:
        """
        Record a ticket classification response and update all internal counters.
        Appends the record to the recent queue.

        Args:
            response (dict): The classification response dictionary.
            timestamp (str): The ISO/UTC string timestamp.
        """
        with self._lock:
            self.total += 1
            
            case_type = response.get("case_type")
            if case_type:
                self.by_case_type[case_type] += 1
                
            severity = response.get("severity")
            if severity:
                self.by_severity[severity] += 1
                
            if response.get("human_review_required"):
                self.human_review_count += 1
                
            self.recent.append({
                "response": response,
                "timestamp": timestamp
            })

    def summary(self) -> dict:
        """
        Returns a JSON-serializable dictionary of all stats counters and queue.

        Returns:
            dict: The system statistics report.
        """
        with self._lock:
            return {
                "total": self.total,
                "by_case_type": dict(self.by_case_type),
                "by_severity": dict(self.by_severity),
                "human_review_count": self.human_review_count,
                "recent": list(self.recent)
            }

    def reset(self) -> None:
        """
        Resets all counters and clears the recent log.
        """
        with self._lock:
            self.total = 0
            self.by_case_type.clear()
            self.by_severity.clear()
            self.human_review_count = 0
            self.recent.clear()
