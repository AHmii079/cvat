// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import { useEffect, useRef, useState } from 'react';

export type LiveStatus =
    | { state: 'connecting' }
    | { state: 'live' }
    | { state: 'reconnecting', retryAt: number };

// The server closes with 4000 + the HTTP status the REST endpoint returned.
// These will not change by retrying, so the page shows them instead of reconnecting.
const PERMANENT_CLOSE_REASONS: Record<number, string> = {
    4401: 'Your session has ended. Log in again to see the counts.',
    4403: 'You no longer have access to the annotations of this task.',
    4404: 'This task no longer exists.',
};

const FIRST_RETRY_MS = 1000;
const MAX_RETRY_MS = 30000;

export function liveLabelCountsUrl(taskId: number, query: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/api/tasks/${taskId}/label-counts/live${query}`;
}

/**
 * Keeps a WebSocket open to `url` while it is not null.
 * Every message is passed to onData. When the connection drops it reconnects after
 * 1 s, 2 s, 4 s ... up to 30 s; the server sends the full current counts as the first
 * message of every connection, so the page is back in sync as soon as it reconnects.
 */
export function useLiveLabelCounts<T>(
    url: string | null,
    onData: (data: T) => void,
    onPermanentClose: (reason: string) => void,
): LiveStatus {
    const [status, setStatus] = useState<LiveStatus>({ state: 'connecting' });
    const handlers = useRef({ onData, onPermanentClose });
    handlers.current = { onData, onPermanentClose };

    useEffect(() => {
        if (!url) {
            return undefined;
        }

        let socket: WebSocket | null = null;
        let retryTimer: number | undefined;
        let failedAttempts = 0;
        let stopped = false;

        const connect = (): void => {
            socket = new WebSocket(url);
            socket.onopen = () => {
                failedAttempts = 0;
                setStatus({ state: 'live' });
            };
            socket.onmessage = (event: MessageEvent<string>) => {
                handlers.current.onData(JSON.parse(event.data));
            };
            socket.onclose = (event: CloseEvent) => {
                if (stopped) {
                    return;
                }
                if (event.code in PERMANENT_CLOSE_REASONS) {
                    handlers.current.onPermanentClose(PERMANENT_CLOSE_REASONS[event.code]);
                    return;
                }
                const delay = Math.min(FIRST_RETRY_MS * 2 ** failedAttempts, MAX_RETRY_MS);
                failedAttempts += 1;
                setStatus({ state: 'reconnecting', retryAt: Date.now() + delay });
                retryTimer = window.setTimeout(connect, delay);
            };
        };

        setStatus({ state: 'connecting' });
        connect();

        return () => {
            stopped = true;
            window.clearTimeout(retryTimer);
            socket?.close();
        };
    }, [url]);

    return status;
}
