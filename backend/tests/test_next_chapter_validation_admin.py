import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from next_chapter.routes import validation_warnings
from next_chapter.validation import warning_sink, warn


def test_admin_diagnostics_require_admin():
    with patch('next_chapter.routes.load_validation_runs') as load:
        with pytest.raises(HTTPException) as caught:
            asyncio.run(validation_warnings(SimpleNamespace(role='user')))
        assert caught.value.status_code == 403
        load.assert_not_called()
        load.return_value = {'runs': [{'id': 'chapter_test', 'warnings': []}]}
        assert asyncio.run(validation_warnings(SimpleNamespace(role='admin'))) == load.return_value


def test_parallel_warning_contexts_do_not_mix_stages():
    async def run():
        async def task(name):
            warnings = []
            token = warning_sink.set(warnings.append)
            try:
                await asyncio.sleep(0)
                warn(name)
                return warnings
            finally:
                warning_sink.reset(token)
        return await asyncio.gather(task('pd_1'), task('pd_2'))
    assert asyncio.run(run()) == [['pd_1'], ['pd_2']]
    assert warning_sink.get() is None
