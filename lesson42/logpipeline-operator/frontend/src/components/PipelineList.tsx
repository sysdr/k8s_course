import React, { useState, useEffect } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Typography
} from '@mui/material';

interface Pipeline {
  name: string;
  namespace: string;
  status: string;
  collectors: number;
  processors: number;
  sinks: number;
}

const PipelineList: React.FC = () => {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);

  useEffect(() => {
    // Fetch pipelines from API
    const mockPipelines: Pipeline[] = [
      {
        name: 'production-logs',
        namespace: 'logging',
        status: 'Running',
        collectors: 3,
        processors: 5,
        sinks: 2
      },
      {
        name: 'audit-logs',
        namespace: 'logging',
        status: 'Running',
        collectors: 2,
        processors: 3,
        sinks: 1
      }
    ];
    setPipelines(mockPipelines);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Running':
        return 'success';
      case 'Failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <div>
      <Typography variant="h5" gutterBottom>
        LogPipeline Resources
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Namespace</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Collectors</TableCell>
              <TableCell align="right">Processors</TableCell>
              <TableCell align="right">Sinks</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {pipelines.map((pipeline) => (
              <TableRow key={pipeline.name}>
                <TableCell>{pipeline.name}</TableCell>
                <TableCell>{pipeline.namespace}</TableCell>
                <TableCell>
                  <Chip
                    label={pipeline.status}
                    color={getStatusColor(pipeline.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">{pipeline.collectors}</TableCell>
                <TableCell align="right">{pipeline.processors}</TableCell>
                <TableCell align="right">{pipeline.sinks}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
};

export default PipelineList;
