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
import Result from 'antd/lib/result';
import Title from 'antd/lib/typography/Title';
import Text from 'antd/lib/typography/Text';
import {
    Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

import { getCore, ServerError } from 'cvat-core-wrapper';
import GoBackButton from 'components/common/go-back-button';
import CVATLoadingSpinner from 'components/common/loading-spinner';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

const core = getCore();

interface LabelCount {
    id: number;
    name: string;
    count: number;
}

interface TaskLabelCounts {
    task_id: number;
    total: number;
    labels: LabelCount[];
}

type PageState =
    | { status: 'loading' }
    | { status: 'error', message: string }
    | { status: 'ready', data: TaskLabelCounts };

const BAR_HEIGHT_PX = 22;

function errorMessage(error: unknown): string {
    if (error instanceof ServerError && error.code === 403) {
        return 'You do not have access to the annotations of this task.';
    }
    if (error instanceof ServerError && error.code === 404) {
        return 'This task does not exist.';
    }
    return error instanceof Error ? error.message : 'The request failed.';
}

function LabelCountsChart({ labels }: { labels: LabelCount[] }): JSX.Element {
    return (
        <div className='cvat-label-counts-chart' style={{ height: labels.length * BAR_HEIGHT_PX + 40 }}>
            <Bar
                data={{
                    labels: labels.map((label) => label.name),
                    datasets: [{
                        label: 'Annotations',
                        data: labels.map((label) => label.count),
                        backgroundColor: '#1890ff',
                    }],
                }}
                options={{
                    indexAxis: 'y',
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: { beginAtZero: true, ticks: { precision: 0 } },
                        y: { ticks: { autoSkip: false } },
                    },
                }}
            />
        </div>
    );
}

function LabelCountsPage(): JSX.Element {
    const taskId = +useParams<{ tid: string }>().tid;
    const [state, setState] = useState<PageState>({ status: 'loading' });

    const fetchCounts = useCallback(async (): Promise<TaskLabelCounts> => {
        const response = await core.server.request(
            `${core.config.backendAPI}/tasks/${taskId}/label-counts`,
            { method: 'GET' },
        ) as { data: TaskLabelCounts };
        return response.data;
    }, [taskId]);

    const load = useCallback((): (() => void) => {
        let active = true;
        setState({ status: 'loading' });
        fetchCounts()
            .then((data) => active && setState({ status: 'ready', data }))
            .catch((error) => active && setState({ status: 'error', message: errorMessage(error) }));
        return () => { active = false; };
    }, [fetchCounts]);

    useEffect(load, [load]);

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
        content = (
            <>
                <Text type='secondary'>
                    {`${state.data.total} annotations across ${state.data.labels.length} labels`}
                </Text>
                <LabelCountsChart labels={state.data.labels} />
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
                    <Title level={4} className='cvat-label-counts-header'>
                        {`Annotations per label — task #${taskId}`}
                    </Title>
                    {content}
                </Col>
            </Row>
        </div>
    );
}

export default React.memo(LabelCountsPage);
