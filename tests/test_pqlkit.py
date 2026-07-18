from pqlkit import explain, format_pql, tokenize


# Examples taken from Adobe's published PQL documentation.
SIMPLE = 'homeAddress.countryISO = "CA"'
COMPOUND = 'homeAddress.countryISO = "CA" and person.birthYear = 1985'
EVENT = 'exists E from xEvent where E.eventType = "commerce.purchases"'
AGGREGATE = (
    'let S = (sum X.commerce.order.priceTotal over X from xEvent '
    'where X.commerce.order.currencyCode = "USD") in (S > 100 and S < 1000)'
)


class TestLexer:
    def test_keeps_dotted_paths_together(self):
        toks = [t.value for t in tokenize(SIMPLE) if t.kind != "ws"]
        assert "homeAddress" in toks and "countryISO" in toks

    def test_string_literal_is_one_token(self):
        toks = [t for t in tokenize(SIMPLE) if t.kind == "string"]
        assert len(toks) == 1
        assert toks[0].value == '"CA"'

    def test_number_literal(self):
        toks = [t for t in tokenize(COMPOUND) if t.kind == "number"]
        assert toks[0].value == "1985"


class TestFormatter:
    def test_short_query_stays_on_one_line(self):
        assert format_pql(SIMPLE) == SIMPLE

    def test_no_space_around_dots(self):
        assert "person.birthYear" in format_pql(COMPOUND)

    def test_boolean_operator_gets_its_own_line(self):
        out = format_pql(COMPOUND)
        assert out.rstrip().splitlines()[0].endswith("and")

    def test_output_is_idempotent(self):
        once = format_pql(COMPOUND)
        assert format_pql(once) == once

    def test_no_tokens_are_dropped(self):
        out = format_pql(AGGREGATE)
        for fragment in ["sum", "xEvent", "currencyCode", "USD", "1000"]:
            assert fragment in out

    def test_empty_input(self):
        assert format_pql("") == ""


class TestExplain:
    def test_attribute_query(self):
        out = explain(SIMPLE)
        assert "profile attributes" in out
        assert "home country" in out
        assert "CA" in out

    def test_compound_reports_and(self):
        out = explain(COMPOUND)
        assert "All of the above" in out
        assert "birth year" in out

    def test_event_query_detected(self):
        out = explain(EVENT)
        assert "at least one matching event" in out

    def test_aggregate_warns_about_scan(self):
        out = explain(AGGREGATE)
        assert "sum" in out
        assert "event history is scanned" in out

    def test_mixed_and_or_warns_about_precedence(self):
        q = 'person.gender = "female" and homeAddress.countryISO = "CA" or person.birthYear = 1985'
        assert "precedence" in explain(q)

    def test_humanizes_unknown_paths(self):
        out = explain('loyalty.tierName = "Gold"')
        assert "tier name" in out
