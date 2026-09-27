"""Run the same regression checks against source and frozen distributions."""
import contextlib
import json
import traceback


def run(report):
    import test_app
    import test_multiselect
    results = {}
    try:
        with open(report.with_suffix('.log'), 'w', encoding='utf-8') as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                for name, test in [('pdf_and_ui', test_app.test), ('multiple_processes', test_multiselect.test)]:
                    test()
                    results[name] = 'passed'
    except Exception:
        results['error'] = traceback.format_exc()
        raise
    finally:
        report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
