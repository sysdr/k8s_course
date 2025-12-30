import React, { useState } from 'react';
import {
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box
} from '@mui/material';
import { createTransaction } from '../services/api';

export default function CreateTransaction({ onSuccess }) {
  const [formData, setFormData] = useState({
    user_id: '',
    amount: '',
    currency: 'USD',
    transaction_type: 'payment',
    description: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createTransaction({
        ...formData,
        amount: parseFloat(formData.amount)
      });
      setFormData({
        user_id: '',
        amount: '',
        currency: 'USD',
        transaction_type: 'payment',
        description: ''
      });
      onSuccess();
    } catch (err) {
      alert('Failed to create transaction: ' + err.message);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        id="user-id"
        name="user_id"
        label="User ID"
        value={formData.user_id}
        onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
        required
        size="small"
        autoComplete="username"
      />
      <TextField
        id="amount"
        name="amount"
        label="Amount"
        type="number"
        value={formData.amount}
        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
        required
        size="small"
        inputProps={{ step: "0.01", min: "0" }}
      />
      <FormControl size="small">
        <InputLabel id="transaction-type-label">Type</InputLabel>
        <Select
          id="transaction-type"
          name="transaction_type"
          labelId="transaction-type-label"
          value={formData.transaction_type}
          onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value })}
          label="Type"
        >
          <MenuItem value="payment">Payment</MenuItem>
          <MenuItem value="refund">Refund</MenuItem>
          <MenuItem value="transfer">Transfer</MenuItem>
        </Select>
      </FormControl>
      <TextField
        id="description"
        name="description"
        label="Description"
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        multiline
        rows={2}
        size="small"
      />
      <Button type="submit" variant="contained" color="primary">
        Create Transaction
      </Button>
    </Box>
  );
}
