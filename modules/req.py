import httpx
import threading
import queue

from typing import Optional, Dict, Callable


class HTTPThreadingClient:
    """
    基于httpx的多线程HTTP客户端
    
    示例：
    >>> client = HTTPThreadingClient(max_thread=4)
    >>> client.get('https://httpbin.org/get')
    >>> client.post('https://httpbin.org/post', json={'key': 'value'})
    """
    
    def __init__(self, max_thread: int = 4, timeout: float = 30.0, 
                default_headers: Optional[Dict] = None):
        """
        初始化多线程HTTP客户端
        
        Args:
            max_thread: 最大线程数
            timeout: 请求超时时间（秒）
            verify: SSL证书验证
            default_headers: 默认请求头
        """
        self.max_thread = max_thread
        self.timeout = timeout
        self.default_headers = default_headers or {}
        
        # 创建线程池
        self.task_queue = queue.Queue()
        self.threads = []
        self._running = True
        self.results = {}  # 存储请求结果
        self.result_lock = threading.Lock()
        self.task_id = 0
        self.task_id_lock = threading.Lock()
        
        self._create_threads()
    
    def _create_threads(self):
        """创建工作线程"""
        for i in range(self.max_thread):
            thread = threading.Thread(
                target=self._worker,
                name=f"HTTPWorker-{i+1}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
    
    def _get_next_task_id(self) -> int:
        """获取下一个任务ID"""
        with self.task_id_lock:
            self.task_id += 1
            return self.task_id
    
    def _worker(self):
        """工作线程函数"""
        while self._running:
            try:
                # 获取任务
                task_id, method, url, kwargs, callback, error_callback = self.task_queue.get(timeout=1)
                
                try:
                    # 执行HTTP请求
                    response = self._execute_request(method, url, **kwargs)
                    
                    # 调用回调函数
                    if callback:
                        callback(response)
                    
                    # 存储结果
                    with self.result_lock:
                        self.results[task_id] = {
                            'success': True,
                            'response': response,
                            'error': None
                        }
                        
                except Exception as e:
                    # 存储错误信息
                    with self.result_lock:
                        self.results[task_id] = {
                            'success': False,
                            'response': None,
                            'error': str(e)
                        }
                    
                    # 调用错误回调
                    if error_callback:
                        error_callback(e)
                
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
    
    def _execute_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """执行HTTP请求"""
        # 设置默认参数
        kwargs.setdefault('timeout', self.timeout)
        
        # 合并请求头
        headers = self.default_headers.copy()
        if 'headers' in kwargs and kwargs['headers']:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # 使用httpx执行请求
        with httpx.Client() as client:
            http_method = getattr(client, method.lower())
            return http_method(url, **kwargs)
    
    def _submit_request(self, method: str, url: str, 
                       callback: Optional[Callable] = None,
                       error_callback: Optional[Callable] = None,
                       **kwargs) -> int:
        """
        提交HTTP请求到线程池
        
        Returns:
            task_id: 任务ID，可用于查询结果
        """
        task_id = self._get_next_task_id()
        
        self.task_queue.put((task_id, method, url, kwargs, callback, error_callback))
        return task_id
    
    def get(self, url: str, params: Optional[Dict] = None, 
            headers: Optional[Dict] = None, 
            callback: Optional[Callable] = None,
            error_callback: Optional[Callable] = None,
            **kwargs) -> int:
        """发送GET请求"""
        kwargs.update({'params': params, 'headers': headers})
        return self._submit_request('get', url, callback, error_callback, **kwargs)
    
    def post(self, url: str, data: Optional[Dict] = None, 
             json: Optional[Dict] = None, 
             headers: Optional[Dict] = None,
             callback: Optional[Callable] = None,
             error_callback: Optional[Callable] = None,
             **kwargs) -> int:
        """发送POST请求"""
        kwargs.update({'data': data, 'json': json, 'headers': headers})
        return self._submit_request('post', url, callback, error_callback, **kwargs)
    
    def put(self, url: str, data: Optional[Dict] = None, 
            json: Optional[Dict] = None,
            headers: Optional[Dict] = None,
            callback: Optional[Callable] = None,
            error_callback: Optional[Callable] = None,
            **kwargs) -> int:
        """发送PUT请求"""
        kwargs.update({'data': data, 'json': json, 'headers': headers})
        return self._submit_request('put', url, callback, error_callback, **kwargs)
    
    def delete(self, url: str, headers: Optional[Dict] = None,
               callback: Optional[Callable] = None,
               error_callback: Optional[Callable] = None,
               **kwargs) -> int:
        """发送DELETE请求"""
        kwargs.update({'headers': headers})
        return self._submit_request('delete', url, callback, error_callback, **kwargs)
    
    def patch(self, url: str, data: Optional[Dict] = None, 
              json: Optional[Dict] = None,
              headers: Optional[Dict] = None,
              callback: Optional[Callable] = None,
              error_callback: Optional[Callable] = None,
              **kwargs) -> int:
        """发送PATCH请求"""
        kwargs.update({'data': data, 'json': json, 'headers': headers})
        return self._submit_request('patch', url, callback, error_callback, **kwargs)
    
    def head(self, url: str, params: Optional[Dict] = None,
             headers: Optional[Dict] = None,
             callback: Optional[Callable] = None,
             error_callback: Optional[Callable] = None,
             **kwargs) -> int:
        """发送HEAD请求"""
        kwargs.update({'params': params, 'headers': headers})
        return self._submit_request('head', url, callback, error_callback, **kwargs)
    
    def options(self, url: str, headers: Optional[Dict] = None,
                callback: Optional[Callable] = None,
                error_callback: Optional[Callable] = None,
                **kwargs) -> int:
        """发送OPTIONS请求"""
        kwargs.update({'headers': headers})
        return self._submit_request('options', url, callback, error_callback, **kwargs)
    
    def get_result(self, task_id: int) -> Optional[Dict]:
        """获取任务结果"""
        with self.result_lock:
            return self.results.get(task_id)
    
    def wait_completion(self, timeout: Optional[float] = None):
        """等待所有任务完成"""
        self.task_queue.join()
    
    def shutdown(self):
        """关闭客户端"""
        self._running = False
        self.wait_completion()
        
        # 等待线程结束
        for thread in self.threads:
            thread.join(timeout=2)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
