import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { deleteTransaction } from '../services/api';

export default function TransactionList({ transactions, onRefresh }) {
  const handleDelete = async (id) => {
    if (window.confirm('Delete this transaction? (Recoverable from backup!)')) {
      try {
        await deleteTransaction(id);
        onRefresh();
      } catch (err) {
        alert('Failed to delete: ' + err.message);
      }
    }
  };

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>User</TableCell>
            <TableCell>Type</TableCell>
            <TableCell align="right">Amount</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Created</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {transactions.map((tx) => (
            <TableRow key={tx.id}>
              <TableCell>{tx.id}</TableCell>
              <TableCell>{tx.user_id}</TableCell>
              <TableCell>{tx.transaction_type}</TableCell>
              <TableCell align="right">
                {tx.amount.toFixed(2)} {tx.currency}
              </TableCell>
              <TableCell>
                <Chip
                  label={tx.status}
                  color={tx.status === 'completed' ? 'success' : 'warning'}
                  size="small"
                />
              </TableCell>
              <TableCell>
                {new Date(tx.created_at).toLocaleString()}
              </TableCell>
              <TableCell>
                <Tooltip title="Delete (recoverable from backup)">
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(tx.id)}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
