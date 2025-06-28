from unittest.mock import Mock, call
from core.dataloader import DataLoader

def make_mock_lock():
    lock = Mock()
    lock.__enter__ = Mock(return_value=lock)
    lock.__exit__ = Mock(return_value=False)
    lock.entered = 0
    lock.exited = 0
    def enter_side_effect(*args, **kwargs):
        lock.entered += 1
        return lock
    def exit_side_effect(*args, **kwargs):
        lock.exited += 1
        return False
    lock.__enter__.side_effect = enter_side_effect
    lock.__exit__.side_effect = exit_side_effect
    return lock

def get_named_lock_factory():
    last_lock = {'lock': None}
    def get_named_lock(name):
        lock = make_mock_lock()
        last_lock['lock'] = lock
        return lock
    get_named_lock.last_lock = last_lock
    return get_named_lock

def test_dataloader_basic():
    backend = Mock()
    backend.get = Mock(side_effect=lambda k: None)
    backend.set = Mock()
    get_named_lock = get_named_lock_factory()
    def batch_fn(keys):
        batch_fn.called = True
        return [k * 2 for k in keys]
    batch_fn.called = False
    from core.logger import Logger
    logger = Logger(level="DEBUG")
    loader = DataLoader(batch_load_fn=batch_fn, backend=backend, get_named_lock=get_named_lock, logger=logger)
    result = loader.load_many([1, 2, 3])
    assert result == [2, 4, 6]
    assert batch_fn.called
    assert backend.get.call_args_list == [call(1), call(2), call(3)]
    assert backend.set.call_args_list == [call(1, 2), call(2, 4), call(3, 6)]
    lock = get_named_lock.last_lock['lock']
    assert lock.entered == 1 and lock.exited == 1
    # Should use cache on second call
    batch_fn2 = Mock(side_effect=lambda keys: [k * 2 for k in keys])
    loader._batch_load_fn = batch_fn2
    # Simulate backend.get returning cached values for 2 and 3, None for 4
    def get_side_effect(key):
        return {2: 4, 3: 6}.get(key, None)
    backend.get.reset_mock()
    backend.set.reset_mock()
    backend.get.side_effect = get_side_effect
    result2 = loader.load_many([2, 3, 4])
    assert result2 == [4, 6, 8]
    # Only key 4 should be fetched by batch_fn2
    batch_fn2.assert_called_once_with([4])
    assert backend.get.call_args_list == [call(2), call(3), call(4)]
    assert backend.set.call_args_list == [call(4, 8)]

def test_dataloader_deduplication():
    backend = Mock()
    backend.get = Mock(side_effect=lambda k: None)
    backend.set = Mock()
    get_named_lock = get_named_lock_factory()
    def batch_fn(keys):
        batch_fn.called = True
        batch_fn.calls.append(keys)
        return [k + 1 for k in keys]
    batch_fn.called = False
    batch_fn.calls = []
    from core.logger import Logger
    logger = Logger(level="DEBUG")
    loader = DataLoader(batch_load_fn=batch_fn, backend=backend, get_named_lock=get_named_lock, logger=logger)
    result = loader.load_many([1, 2, 2, 3, 1])
    assert result == [2, 3, 3, 4, 2]
    assert batch_fn.called
    assert batch_fn.calls == [[1, 2, 3]]
    # backend.get should be called for each input key (including duplicates)
    assert backend.get.call_args_list == [call(1), call(2), call(2), call(3), call(1)]
    # backend.set should be called for each unique key
    assert backend.set.call_args_list == [call(1, 2), call(2, 3), call(3, 4)]
    lock = get_named_lock.last_lock['lock']
    assert lock.entered == 1 and lock.exited == 1
