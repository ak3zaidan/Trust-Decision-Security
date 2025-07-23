package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/bogdanfinn/fhttp/cookiejar"
	"github.com/bogdanfinn/tls-client/profiles"

	fhttp "github.com/bogdanfinn/fhttp"
	tls_client "github.com/bogdanfinn/tls-client"
)

var USE_CHARLES bool = false

var profile profiles.ClientProfile = profiles.Chrome_133

type RequestPayload struct {
	URL         string            `json:"url"`
	Data        string            `json:"data"`
	Headers     map[string]string `json:"headers"`
	HeaderOrder []string          `json:"header_order"`
	ProxyURL    string            `json:"proxy_url"`
}

func main() {
	var payload RequestPayload
	if err := json.NewDecoder(os.Stdin).Decode(&payload); err != nil {
		fmt.Fprintln(os.Stderr, "Failed to decode input:", err)
		os.Exit(1)
	}

	client, clientError := getClient(payload.ProxyURL)
	if clientError != nil {
		fmt.Fprintln(os.Stderr, "Failed to make client", clientError)
		os.Exit(1)
	}

	req, err := fhttp.NewRequest(http.MethodPost, payload.URL, bytes.NewBufferString(payload.Data))
	if err != nil {
		fmt.Fprintln(os.Stderr, "Failed to build request:", err)
		os.Exit(1)
	}

	h := fhttp.Header{}

	for key, val := range payload.Headers {
		h[key] = []string{val}
	}

	h[fhttp.HeaderOrderKey] = payload.HeaderOrder

	req.Header = h

	resp, err := client.Do(req)
	if err != nil {
		fmt.Fprintln(os.Stderr, "Request error:", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}

func getClient(proxyURL string) (tls_client.HttpClient, error) {
	jar, _ := cookiejar.New(nil)

	options := []tls_client.HttpClientOption{
		tls_client.WithTimeoutSeconds(20),
		tls_client.WithClientProfile(profile),
		tls_client.WithInsecureSkipVerify(),
		tls_client.WithCookieJar(jar),
		tls_client.WithRandomTLSExtensionOrder(),
	}

	if USE_CHARLES {
		options = append(options,
			tls_client.WithCharlesProxy("127.0.0.1", "8888"),
		)
	} else if proxyURL != "" {
		options = append(options, tls_client.WithProxyUrl(proxyURL))
	}

	client, err := tls_client.NewHttpClient(tls_client.NewNoopLogger(), options...)
	if err != nil {
		return nil, err
	}

	return client, nil
}
