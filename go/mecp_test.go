package mecp

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type vectorFile struct {
	Decode []struct {
		Name   string          `json:"name"`
		Input  string          `json:"input"`
		Expect json.RawMessage `json:"expect"`
	} `json:"decode"`
	Encode []struct {
		Name     string          `json:"name"`
		Severity int             `json:"severity"`
		Codes    []string        `json:"codes"`
		Freetext *string         `json:"freetext"`
		Expect   json.RawMessage `json:"expect"`
	} `json:"encode"`
	Validate []struct {
		Name   string          `json:"name"`
		Input  string          `json:"input"`
		Expect json.RawMessage `json:"expect"`
	} `json:"validate"`
}

func readJSON(t *testing.T, path string, v any) {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(raw, v); err != nil {
		t.Fatal(err)
	}
}

func loadVectors(t *testing.T) vectorFile {
	var v vectorFile
	readJSON(t, "../vectors/mecp-vectors.json", &v)
	return v
}

// sameJSON compares got (marshalled) with want as generic JSON values.
func sameJSON(t *testing.T, name string, got any, want json.RawMessage) {
	t.Helper()
	g, err := json.Marshal(got)
	if err != nil {
		t.Fatal(err)
	}
	var gv, wv any
	if err := json.Unmarshal(g, &gv); err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(want, &wv); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(gv, wv) {
		t.Errorf("%s:\n got  %s\n want %s", name, g, want)
	}
}

func TestDecodeVectors(t *testing.T) {
	for _, c := range loadVectors(t).Decode {
		sameJSON(t, c.Name, Decode(c.Input), c.Expect)
	}
}

func TestEncodeVectors(t *testing.T) {
	for _, c := range loadVectors(t).Encode {
		codes := c.Codes
		if codes == nil {
			codes = []string{}
		}
		sameJSON(t, c.Name, Encode(c.Severity, codes, c.Freetext), c.Expect)
	}
}

func TestValidateVectors(t *testing.T) {
	for _, c := range loadVectors(t).Validate {
		sameJSON(t, c.Name, Validate(c.Input), c.Expect)
	}
}

// TestUpstreamFreetext runs mecp-org/MECP freetext/tests.json unchanged.
func TestUpstreamFreetext(t *testing.T) {
	var manifest struct {
		SchemaVersion int `json:"schemaVersion"`
	}
	readJSON(t, "../upstream/freetext/manifest.json", &manifest)
	if manifest.SchemaVersion != 1 {
		t.Fatalf("unsupported schemaVersion %d", manifest.SchemaVersion)
	}
	var tests []struct {
		Title  string                     `json:"title"`
		Input  string                     `json:"input"`
		Expect map[string]json.RawMessage `json:"expect"`
	}
	readJSON(t, "../upstream/freetext/tests.json", &tests)
	fields := []string{"pax", "gps", "timestamp", "language", "callsign", "reference", "duration"}
	for _, c := range tests {
		d := Decode(c.Input)
		if c.Expect == nil {
			if d.Valid {
				t.Errorf("%s: decoded as valid", c.Title)
			}
			continue
		}
		if !d.Valid {
			t.Errorf("%s: not valid", c.Title)
			continue
		}
		want := map[string]json.RawMessage{}
		for _, f := range fields {
			want[f] = json.RawMessage("null")
			if v, ok := c.Expect[f]; ok {
				want[f] = v
			}
		}
		w, _ := json.Marshal(want)
		sameJSON(t, c.Title, d.Extracted, w)
	}
}

func TestBeaconHelpers(t *testing.T) {
	codes := Decode("MECP/0/B01 B02 B03").Codes
	if !IsBeacon(codes) || !IsBeaconAck(codes) || !IsBeaconCancel(codes) {
		t.Fatal("beacon codes not detected")
	}
	if IsBeacon([]string{"M01"}) {
		t.Fatal("false positive")
	}
}
