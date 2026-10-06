// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';

import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { Link } from 'react-router-dom';
import { Row, Col } from 'antd/lib/grid';
import Button from 'antd/lib/button';
import Empty from 'antd/lib/empty';
import Radio from 'antd/lib/radio';
import Result from 'antd/lib/result';
import Tag from 'antd/lib/tag';
import Title from 'antd/lib/typography/Title';
import Text from 'antd/lib/typography/Text';
import {
    Chart as ChartJS, BarElement, CategoryScale, Legend, LinearScale, Tooltip,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

import { getCore, ServerError } from 'cvat-core-wrapper';
import GoBackButton from 'components/common/go-back-button';
import CVATLoadingSpinner from 'components/common/loading-spinner';
import { LiveStatus, liveLabelCountsUrl, useLiveLabelCounts } from './use-live-label-counts';

ChartJS.register(BarElement, CategoryScale, Legend, LinearScale, Tooltip);

const core = getCore();

interface LabelCount {
    id: number;
    name: string;
    count: number;
    by_shape_type?: Record<string, number>;
}

interface TaskLabelCounts {
    task_id: number;
    total: number;
    group_by: 'shape_type' | null;
    labels: LabelCount[];
}

type Grouping = 'total' | 'shape_type';

type PageState =
    | { status: 'loading' }
    | { status: 'error', message: string }
    | { status: 'ready', data: TaskLabelCounts };

const BAR_HEIGHT_PX = 22;
const TOTAL_COLOR = '#1890ff';
const SHAPE_TYPE_COLORS: Record<string, string> = {
    rectangle: '#1890ff',
    polygon: '#52c41a',
    mask: '#fa8c16',
    polyline: '#722ed1',
    points: '#eb2f96',
    ellipse: '#13c2c2',
    cuboid: '#a0d911',
    skeleton: '#8c8c8c',
};

function shapeTypeTotals(labels: LabelCount[]): [string, number][] {
    const totals: Record<string, number> = {};
    for (const label of labels) {
        for (const [type, count] of Object.entries(label.by_shape_type ?? {})) {
            totals[type] = (totals[type] ?? 0) + count;
        }
    }
    return Object.entries(totals).sort(([, a], [, b]) => b - a);
}

function errorMessage(error: unknown): string {
    if (error instanceof ServerError && error.code === 403) {
        return 'You do not have access to the annotations of this task.';
    }
    if (error instanceof ServerError && error.code === 404) {
        return 'This task does not exist.';
    }
    return error instanceof Error ? error.message : 'The request failed.';
}

function LiveStatusTag({ status }: { status: LiveStatus }): JSX.Element {
    if (status.state === 'live') {
        return <Tag className='cvat-label-counts-live' color='green'>Live</Tag>;
    }
    if (status.state === 'reconnecting') {
        return (
            <Tag className='cvat-label-counts-live' color='orange'>
                {`Connection lost, retrying in ${status.retryInSeconds} s`}
            </Tag>
        );
    }
    return <Tag className='cvat-label-counts-live'>Connecting…</Tag>;
}

function LabelCountsChart({ data }: { data: TaskLabelCounts }): JSX.Element {
    const { labels } = data;
    const byShapeType = data.group_by === 'shape_type';
    const datasets = byShapeType ?
        shapeTypeTotals(labels).map(([type]) => ({
            label: type,
            data: labels.map((label) => label.by_shape_type?.[type] ?? 0),
            backgroundColor: SHAPE_TYPE_COLORS[type] ?? '#bfbfbf',
        })) :
        [{ label: 'Annotations', data: labels.map((label) => label.count), backgroundColor: TOTAL_COLOR }];

    return (
        <div className='cvat-label-counts-chart' style={{ height: labels.length * BAR_HEIGHT_PX + 60 }}>
            <Bar
                data={{ labels: labels.map((label) => label.name), datasets }}
                options={{
                    indexAxis: 'y',
                    maintainAspectRatio: false,
                    animation: false,
                    plugins: { legend: { display: byShapeType, position: 'top' } },
                    scales: {
                        x: { beginAtZero: true, stacked: byShapeType, ticks: { precision: 0 } },
                        y: { stacked: byShapeType, ticks: { autoSkip: false } },
                    },
                }}
            />
        </div>
    );
}

function LabelCountsPage(): JSX.Element {
    const taskId = +useParams<{ tid: string }>().tid;
    const [state, setState] = useState<PageState>({ status: 'loading' });
    const [grouping, setGrouping] = useState<Grouping>('total');

    const query = grouping === 'shape_type' ? '?group_by=shape_type' : '';

    const fetchCounts = useCallback(async (): Promise<TaskLabelCounts> => {
        const response = await core.server.request(
            `${core.config.backendAPI}/tasks/${taskId}/label-counts${query}`,
            { method: 'GET' },
        ) as { data: TaskLabelCounts };
        return response.data;
    }, [taskId, query]);

    const load = useCallback((): (() => void) => {
        let active = true;
        setState({ status: 'loading' });
        fetchCounts()
            .then((data) => active && setState({ status: 'ready', data }))
            .catch((error) => active && setState({ status: 'error', message: errorMessage(error) }));
        return () => { active = false; };
    }, [fetchCounts]);

    useEffect(load, [load]);

    const liveStatus = useLiveLabelCounts<TaskLabelCounts>(
        state.status === 'ready' ? liveLabelCountsUrl(taskId, query) : null,
        (data) => setState({ status: 'ready', data }),
        (reason) => setState({ status: 'error', message: reason }),
    );

    let content: JSX.Element;
    if (state.status === 'loading') {
        content = <CVATLoadingSpinner />;
    } else if (state.status === 'error') {
        content = (
            <Result
                className='cvat-label-counts-error'
                status='error'
                title='Could not load annotation counts'
                subTitle={state.message}
                extra={<Button type='primary' onClick={load}>Retry</Button>}
            />
        );
    } else if (state.data.total === 0) {
        content = (
            <Empty
                className='cvat-label-counts-empty'
                description={(
                    <>
                        <Text>This task has no annotations yet.</Text>
                        <br />
                        <Link to={`/tasks/${taskId}`}>Open the task to start annotating</Link>
                    </>
                )}
            />
        );
    } else {
        const typeSummary = shapeTypeTotals(state.data.labels)
            .map(([type, count]) => `${type} ${count}`)
            .join(', ');
        content = (
            <>
                <div className='cvat-label-counts-summary'>
                    <Text type='secondary'>
                        {`${state.data.total} annotations across ${state.data.labels.length} labels`}
                        {typeSummary && ` (${typeSummary})`}
                    </Text>
                    <LiveStatusTag status={liveStatus} />
                </div>
                <LabelCountsChart data={state.data} />
            </>
        );
    }

    return (
        <div className='cvat-label-counts-page'>
            <Row justify='center'>
                <Col span={22} xl={18} xxl={14} className='cvat-task-top-bar'>
                    <GoBackButton />
                </Col>
            </Row>
            <Row justify='center' className='cvat-label-counts-inner-wrapper'>
                <Col span={22} xl={18} xxl={14} className='cvat-label-counts-inner'>
                    <Row justify='space-between' align='middle' className='cvat-label-counts-header'>
                        <Title level={4}>{`Annotations per label — task #${taskId}`}</Title>
                        <Radio.Group
                            className='cvat-label-counts-grouping'
                            optionType='button'
                            buttonStyle='solid'
                            value={grouping}
                            onChange={(event) => setGrouping(event.target.value)}
                            options={[
                                { label: 'Total', value: 'total' },
                                { label: 'By shape type', value: 'shape_type' },
                            ]}
                        />
                    </Row>
                    {content}
                </Col>
            </Row>
        </div>
    );
}

export default React.memo(LabelCountsPage);
