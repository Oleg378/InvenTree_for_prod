import { t } from '@lingui/macro';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ModelType } from '../../render/ModelType';
import { TableStatusRenderer } from '../../renderers/StatusRenderer';
import { InvenTreeTable } from '../InvenTreeTable';

export function SalesOrderTable({ params }: { params?: any }) {
  const { tableKey } = useTableRefresh('sales-order');

  const navigate = useNavigate();

  // TODO: Custom filters

  // TODO: Row actions

  // TODO: Table actions (e.g. create new sales order)

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'reference',
        title: t`Sales Order`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'description',
        title: t`Description`,
        switchable: true
      },
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: function (record: any) {
          let customer = record.customer_detail ?? {};

          return (
            <Thumbnail
              src={customer?.image}
              alt={customer.name}
              text={customer.name}
            />
          );
        }
      },
      {
        accessor: 'customer_reference',
        title: t`Customer Reference`,
        switchable: true
      },
      {
        accessor: 'project_code',
        title: t`Project Code`,
        switchable: true
        // TODO: Custom formatter
      },
      {
        accessor: 'status',
        title: t`Status`,
        sortable: true,
        switchable: true,
        render: TableStatusRenderer(ModelType.salesorder)
      }

      // TODO: Creation date
      // TODO: Target date
      // TODO: Shipment date
      // TODO: Line items
      // TODO: Total price
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.sales_order_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          customer_detail: true
        },
        onRowClick: (row: any) => {
          if (row.pk) {
            navigate(`/sales/sales-order/${row.pk}/`);
          }
        }
      }}
    />
  );
}