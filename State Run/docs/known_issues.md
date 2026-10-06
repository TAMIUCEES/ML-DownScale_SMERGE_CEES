# Known issues and methodology caveats

These are in the working scripts and are left as they are so results stay comparable. They are
worth fixing before treating test metrics as unbiased.

1. **XGBoost uses the test shard for early stopping and tuning.** `eval_set` is the test data in
   both the Optuna objective and the final fit, and the objective returns test RMSE. Fix: hold out
   a validation split from the training shard, as the PyTorch scripts do.

2. **Random Forest tuning uses the test shard.** The 50,000-row tuning subsample comes from the
   test shard on rank 0, so hyperparameters are selected on test data. Fix: sample the training
   shard instead.

3. **Per-rank models are independent.** Each rank sees 1/N of the data and predicts only its own
   test shard. There is no ensemble or gradient averaging, so per-rank metrics are not directly
   comparable to one model trained on all data.

4. **The printed Spearman value is coarse.** It averages anomalies to roughly one value per month
   before correlating, and its climatology comes from the shard itself.

5. **SHAP samples in the PyTorch scripts are the first 500 rows** of each shard, which may not be
   representative if the files are ordered by date or location.

6. **TabNet and TFT contain unused parameters** (see `docs/models.md`). They do not affect
   predictions.

7. **The PyTorch scripts accept `parting` but ignore it**, so a second pass with the same state
   overwrites the first unless the version tag in the script is changed.
