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

func loadVectors(t *testing.T) vectorFile {
	t.Helper()
	raw, err := os.ReadFile("../vectors/mecp-vectors.json")
	if err != nil {
		t.Fatal(err)
	}
	var v vectorFile
	if err := json.Unmarshal(raw, &v); err != nil {
		t.Fatal(err)
	}
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

func TestBeaconHelpers(t *testing.T) {
	codes := Decode("MECP/0/B01 B02 B03").Codes
	if !IsBeacon(codes) || !IsBeaconAck(codes) || !IsBeaconCancel(codes) {
		t.Fatal("beacon codes not detected")
	}
	if IsBeacon([]string{"M01"}) {
		t.Fatal("false positive")
	}
}
